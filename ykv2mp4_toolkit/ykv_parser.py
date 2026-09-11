"""优酷 YKV 文件格式解析器。

基于 RainVenturer/YKV-Cracker 的 parser.py 适配。
YKV 文件结构：
    [JPEG 封面图]
    [YK 段头(32B) + 2B 前缀 + 加密 TS 数据 段1]
    [YK 段头(32B) + 2B 前缀 + 加密 TS 数据 段2]
    ...
    [URL 编码的 JSON 尾（段索引 + DRM 密钥）]
    [16 字节 JSON 大小]
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from typing import Any, List
from urllib.parse import unquote

# 每段开头有 32 字节 YK 头 + 2 字节前缀
SEGMENT_OVERHEAD = 34


@dataclass
class YKVFile:
    """已解析的 YKV 文件结构。"""
    path: str
    file_size: int
    segments: List[dict] = field(default_factory=list)
    metadata: Any = None
    encrypted_segments: List[bytes] = field(default_factory=list)
    encryptR_server: str = ""
    copyright_key: str = ""
    clientR1: str = ""


class YKVParser:
    """YouKu YKV 文件解析器。"""

    def parse(self, path: str) -> YKVFile:
        if not os.path.exists(path):
            raise FileNotFoundError(f"YKV 文件不存在: {path}")

        file_size = os.path.getsize(path)
        result = YKVFile(path=path, file_size=file_size)

        with open(path, "rb") as f:
            data = f.read()

        # 步骤 1: 从文件末尾读取 JSON 尾
        # 格式: 最后 16 字节 = URL 编码 JSON 的 ASCII 大小
        json_size_str = (
            data[-16:].decode("ascii", errors="replace").strip()
            .split("\x00", 1)[0].strip()
        )
        json_size = int(json_size_str)
        json_encoded_start = file_size - 16 - json_size
        json_encoded = data[json_encoded_start:file_size - 16]
        json_decoded = unquote(json_encoded.decode("utf-8"))
        json_array = json.loads(json_decoded)

        result.metadata = json_array

        # 步骤 2: 提取 DRM 字段
        self._extract_drm_fields(json_array, result)

        # 步骤 3: 提取所有 TS 分段（按数字文件名排序 = PTS 顺序）
        ts_entries = sorted(
            [e for e in json_array
             if isinstance(e, dict) and e.get("name", "").endswith(".ts")],
            key=lambda e: int(e["name"].replace(".ts", "")),
        )

        # 步骤 4: 提取 TS 数据（去掉 34 字节段头）
        result.segments = ts_entries
        result.encrypted_segments = []
        for entry in ts_entries:
            off = entry["offset"]
            sz = entry["size"]
            chunk_start = off + SEGMENT_OVERHEAD
            chunk_end = off + sz
            result.encrypted_segments.append(data[chunk_start:chunk_end])

        return result

    @staticmethod
    def _extract_drm_fields(json_array: list, result: YKVFile) -> None:
        """从 dbInfo 条目提取 DRM 字段。

        真实 YKV 文件存储元数据在 name=="dbInfo" 的条目中，
        DRM 子字段在 info.configInfo.ups.data.data.stream[*]。
        """
        db_entry = None
        for entry in json_array:
            if isinstance(entry, dict) and entry.get("name") == "dbInfo":
                db_entry = entry
                break
        if db_entry is None:
            return

        info = db_entry.get("info", {})
        config_info = info.get("configInfo", {})
        result.clientR1 = config_info.get("R1Random", "")

        try:
            streams = config_info["ups"]["data"]["data"]["stream"]
        except (KeyError, TypeError, IndexError):
            return

        if streams:
            stream0 = streams[0]
            result.encryptR_server = stream0.get("encryptR_server", "")
            stream_ext = stream0.get("stream_ext", {})
            result.copyright_key = stream_ext.get("copyright_key", "")
