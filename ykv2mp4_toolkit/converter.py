"""FFmpeg-based TS → MP4 转换器。

每个 YKV 分段都是独立的 TS 流，PTS 从 0 开始。
直接拼接会打乱帧序；使用 ffmpeg 的 concat demuxer 会自动
调整 PTS 使播放顺序连续。
"""
from __future__ import annotations
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Optional

TS_PACKET_SIZE = 188


def _get_exe_dir() -> Optional[str]:
    """获取 exe/脚本所在目录（PyInstaller 和源码模式通用）。"""
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后：sys.executable 是 exe 路径
        return os.path.dirname(os.path.abspath(sys.executable))
    # 源码模式：__file__ 是 converter.py 路径
    return os.path.dirname(os.path.abspath(__file__))


def find_ffmpeg() -> Optional[str]:
    """定位系统中的 ffmpeg 可执行文件。

    查找顺序：
        1. 与 exe 同目录的 ffmpeg.exe（便携包场景）
        2. PyInstaller 单文件内捆绑的 ffmpeg（_MEIPASS）
        3. 工具包源码目录旁的 refs/.../ffmpeg.exe（开发场景）
        4. PATH 中的 ffmpeg
        5. 常见 Windows 安装路径
    """
    # 1. 与 exe 同目录（便携包场景：dist/ 下同时有 ykv2mp4.exe + ffmpeg.exe）
    exe_dir = _get_exe_dir()
    if exe_dir:
        same_dir = os.path.join(exe_dir, "ffmpeg.exe")
        if os.path.exists(same_dir):
            return same_dir
        sub = os.path.join(exe_dir, "ffmpeg", "ffmpeg.exe")
        if os.path.exists(sub):
            return sub

    # 2. PyInstaller 单文件模式：_MEIPASS 临时解压目录
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        bundled = os.path.join(meipass, "ffmpeg", "ffmpeg.exe")
        if os.path.exists(bundled):
            return bundled
        bundled2 = os.path.join(meipass, "ffmpeg.exe")
        if os.path.exists(bundled2):
            return bundled2

    # 3. 工具包源码目录旁的 refs/（开发场景）
    here = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.dirname(here)
    bundled_paths = [
        os.path.join(workspace_root, "refs", "ykv转mp4+8.1",
                     "ykv转mp4 8.1", "ffmpeg", "ffmpeg.exe"),
        os.path.join(workspace_root, "refs", "ykv2mp4", "ykv2mp4",
                     "ffmpeg", "ffmpeg.exe"),
        os.path.join(here, "ffmpeg", "ffmpeg.exe"),
    ]
    for path in bundled_paths:
        if os.path.exists(path):
            return path

    # 4. PATH
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    # 5. 常见 Windows 路径
    win_paths = [
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    ]
    for path in win_paths:
        if os.path.exists(path):
            return path

    return None


def _validate_segments(segments: list[bytes]) -> None:
    """校验每段首字节是 TS 同步字 (0x47)。"""
    if not segments:
        raise ValueError("没有可转换的分段")
    for i, seg in enumerate(segments):
        if len(seg) > 0 and seg[0] != 0x47:
            raise ValueError(
                f"分段 {i}: 首字节不是 TS sync byte (0x47)，实际为 0x{seg[0]:02x}"
            )


def ts_segments_to_mp4(
    segments: list[bytes],
    output_path: str,
    ffmpeg_path: str = "ffmpeg",
    keep_ts: bool = False,
    ts_out_path: Optional[str] = None,
) -> str:
    """将多个 TS 分段合并并转换为 MP4。

    使用 ffmpeg concat demuxer，每个分段独立处理 PTS，
    避免直接二进制拼接导致的帧序混乱。

    Args:
        segments: TS 数据分段列表（每个元素是一个独立 TS 流）。
        output_path: 目标 MP4 路径。
        ffmpeg_path: ffmpeg 可执行文件路径。
        keep_ts: 是否保留中间 TS 文件。
        ts_out_path: 若 keep_ts=True，指定中间 TS 路径；None 则用临时文件。

    Returns:
        成功时返回 output_path。

    Raises:
        ValueError: 分段为空或格式错误。
        RuntimeError: ffmpeg 转换失败。
    """
    _validate_segments(segments)

    temp_dir = tempfile.mkdtemp(prefix="ykv_")
    concat_file = os.path.join(temp_dir, "concat.txt")
    temp_files: list[str] = []

    try:
        # 1. 写出每个分段为临时 TS 文件
        for i, seg in enumerate(segments):
            ts_path = os.path.join(temp_dir, f"{i:04d}.ts")
            with open(ts_path, "wb") as f:
                f.write(seg)
            temp_files.append(ts_path)

        # 2. 生成 concat 列表文件（使用 ffmpeg 安全格式）
        with open(concat_file, "w", encoding="utf-8") as f:
            for ts_path in temp_files:
                escaped = ts_path.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")

        # 3. 确保输出目录存在
        out_dir = os.path.dirname(os.path.abspath(output_path))
        os.makedirs(out_dir, exist_ok=True)

        # 4. 调用 ffmpeg concat demuxer 复用为 MP4
        cmd = [
            ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            "-movflags", "+faststart",
            output_path,
        ]
        proc = subprocess.run(cmd, capture_output=True)

        if proc.returncode != 0:
            stderr_text = ""
            if proc.stderr:
                stderr_text = proc.stderr.decode("utf-8", errors="replace")[:800]
            raise RuntimeError(
                f"ffmpeg 失败 (exit {proc.returncode}):\n{stderr_text}"
            )

        if not os.path.exists(output_path):
            raise RuntimeError(f"未生成输出文件: {output_path}")

        # 5. 可选：保留合并后的 TS 文件
        if keep_ts:
            if ts_out_path is None:
                ts_out_path = os.path.splitext(output_path)[0] + ".ts"
            # 用 ffmpeg 直接合并输出一份 TS
            ts_cmd = [
                ffmpeg_path, "-y",
                "-f", "concat", "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                "-bsf:v", "h264_mp4toannexb",
                ts_out_path,
            ]
            subprocess.run(ts_cmd, capture_output=True)

        return output_path

    finally:
        if not keep_ts:
            shutil.rmtree(temp_dir, ignore_errors=True)


def ts_to_mp4(
    ts_data: bytes,
    output_path: str,
    ffmpeg_path: str = "ffmpeg",
) -> str:
    """转换单个 TS blob 为 MP4（单分段场景的便捷封装）。"""
    return ts_segments_to_mp4([ts_data], output_path, ffmpeg_path)
