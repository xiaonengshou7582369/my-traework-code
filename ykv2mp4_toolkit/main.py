"""优酷 YKV → MP4 转换工具包主入口。

用法:
    # 单文件转换（自动暴力枚举 part1）
    python -m ykv2mp4_toolkit.main "D:\\...\\第1集.x.ykv"

    # 单文件 + 指定 part1
    python -m ykv2mp4_toolkit.main "D:\\...\\第1集.x.ykv" --part1 967436

    # 单文件 + 指定输出路径
    python -m ykv2mp4_toolkit.main "D:\\...\\第1集.x.ykv" -o out.mp4

    # 单文件 + 完整 key_string
    python -m ykv2mp4_toolkit.main "D:\\...\\第1集.x.ykv" \
        --key-string "967436,<encryptR_server>,<copyright_key>"

    # 批量处理目录下所有 .ykv 文件
    python -m ykv2mp4_toolkit.main "D:\\Youku Files\\download\\沧元图" -b

    # 批量处理 + 输出到指定目录
    python -m ykv2mp4_toolkit.main "D:\\Youku Files\\download\\沧元图" -b -O "D:\\out"

    # 保留中间 TS 文件
    python -m ykv2mp4_toolkit.main "D:\\...\\第1集.x.ykv" --keep-ts

DRM 密钥管线（来自 aliplayerVS.dll 逆向）：
    key_string = "part1,encryptR_server,copyright_key"
    part1 是 6 位数字，可用 --find-part1 暴力枚举（约 2-3 分钟）
"""
from __future__ import annotations
import argparse
import os
import sys
import time
from typing import List, Optional

from ykv2mp4_toolkit.ykv_parser import YKVParser
from ykv2mp4_toolkit.ykv_decrypt import (
    setup_decryption,
    decrypt_ts_ecb,
    find_part1,
)
from ykv2mp4_toolkit.converter import find_ffmpeg, ts_segments_to_mp4


# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ykv2mp4",
        description="优酷 YKV → MP4 转换工具（含 copyrightDRM 解密）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", nargs="+", help="YKV 文件或目录")
    parser.add_argument("-o", "--output", help="输出 MP4 路径（仅单文件）")
    parser.add_argument("-O", "--output-dir", help="批量模式输出目录")
    parser.add_argument("-b", "--batch", action="store_true",
                        help="批量处理目录下所有 .ykv 文件")
    parser.add_argument("--ffmpeg", help="指定 ffmpeg 路径（默认自动查找）")
    parser.add_argument("--keep-ts", action="store_true",
                        help="保留中间合并的 TS 文件")

    key_group = parser.add_mutually_exclusive_group()
    key_group.add_argument("--key-string", metavar="KEY",
                           help='完整 key_string "part1,encryptR_server,copyright_key"')
    key_group.add_argument("--part1", metavar="DIGITS",
                           help="6 位 part1 数字（part2/part3 从 YKV 读取）")
    key_group.add_argument("--find-part1", action="store_true",
                           help="暴力枚举 part1（约 2-3 分钟，每个文件只需一次）")
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# 单文件处理
# ---------------------------------------------------------------------------
def _build_key_string(ykv, args: argparse.Namespace) -> tuple[str, str]:
    """构造 "part1,encryptR_server,copyright_key" 字符串。

    返回 (key_string, part1_for_cache)。
    part1_for_cache 为空字符串表示无法缓存。
    """
    if args.key_string:
        return args.key_string, ""

    enc_r = ykv.encryptR_server
    cpy_k = ykv.copyright_key
    if not enc_r or not cpy_k:
        raise ValueError(
            "YKV 尾部缺少 encryptR_server / copyright_key 字段。"
            "请用 --key-string 直接提供完整密钥串。"
        )

    if args.part1:
        return f"{args.part1},{enc_r},{cpy_k}", args.part1

    if args.find_part1:
        # 暴力枚举 part1
        print("  暴力枚举 part1（0-999999）...")
        t0 = time.time()
        part1 = find_part1(
            enc_r, cpy_k,
            progress_callback=lambda p: print(f"    {p}%", end="\r"),
        )
        if not part1:
            raise ValueError("未能找到有效的 part1，请用 --key-string 手动提供")
        elapsed = time.time() - t0
        print(f"    找到 part1={part1}（耗时 {elapsed:.1f}s）")
        return f"{part1},{enc_r},{cpy_k}", part1

    raise ValueError(
        "需要提供 part1。可用 --part1 指定 6 位数字、"
        "--key-string 提供完整密钥串、或 --find-part1 暴力枚举。"
    )


def process_file(
    input_path: str,
    output_path: Optional[str],
    ffmpeg_path: str,
    keep_ts: bool,
    args: argparse.Namespace,
    cached_part1: str = "",
) -> str:
    """处理单个 YKV 文件：解析 → 解密 → 转换。"""
    print(f"\n处理: {os.path.basename(input_path)}")

    # 1. 解析 YKV
    parser = YKVParser()
    ykv = parser.parse(input_path)
    print(f"  文件大小: {ykv.file_size:,} 字节 "
          f"({ykv.file_size/1024/1024:.1f} MB)")
    print(f"  分段数: {len(ykv.encrypted_segments)}")
    print(f"  encryptR_server: {ykv.encryptR_server or '(未找到)'}")
    print(f"  copyright_key:   {ykv.copyright_key or '(未找到)'}")

    # 2. 构造 key_string
    # 优先复用缓存 part1（同剧集系列所有文件通常相同）
    if cached_part1 and not args.key_string and not args.part1 \
            and not args.find_part1 and ykv.encryptR_server and ykv.copyright_key:
        key_string = f"{cached_part1},{ykv.encryptR_server},{ykv.copyright_key}"
        print(f"  复用 part1={cached_part1}")
    else:
        key_string, new_part1 = _build_key_string(ykv, args)
        if new_part1 and not cached_part1:
            # 缓存以便后续文件复用
            args._cached_part1 = new_part1  # noqa: SLF001

    # 3. 派生 AES 密钥
    print("  派生 AES-128 密钥...")
    aes_key = setup_decryption(key_string)
    print(f"  AES 密钥: {aes_key.hex()}")

    # 4. 解密所有分段
    total = len(ykv.encrypted_segments)
    print(f"  解密 {total} 个分段...")
    decrypted_segments: list[bytes] = []
    for i, seg in enumerate(ykv.encrypted_segments):
        decrypted_segments.append(decrypt_ts_ecb(seg, aes_key))
        if (i + 1) % 20 == 0 or i + 1 == total:
            print(f"    {i+1}/{total}")
    print(f"  解密完成")

    # 5. 确定输出路径
    if not output_path:
        base = os.path.splitext(os.path.basename(input_path))[0]
        out_dir = args.output_dir or os.path.dirname(input_path)
        output_path = os.path.join(out_dir, f"{base}.mp4")

    # 6. 合并为 MP4
    ts_out = None
    if keep_ts:
        ts_out = os.path.splitext(output_path)[0] + ".ts"
    print(f"  转换为 MP4: {output_path}")
    result = ts_segments_to_mp4(
        decrypted_segments, output_path, ffmpeg_path,
        keep_ts=keep_ts, ts_out_path=ts_out,
    )

    out_size = os.path.getsize(result)
    print(f"  完成! 输出大小: {out_size:,} 字节 "
          f"({out_size/1024/1024:.1f} MB)")
    return result


# ---------------------------------------------------------------------------
# 批量处理
# ---------------------------------------------------------------------------
def process_batch(args: argparse.Namespace, ffmpeg_path: str) -> int:
    """批量处理目录下所有 .ykv 文件。"""
    input_dir = args.input[0]
    if not os.path.isdir(input_dir):
        print(f"错误: 不是目录: {input_dir}", file=sys.stderr)
        return 1

    ykv_files = sorted(
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.lower().endswith(".ykv")
    )

    if not ykv_files:
        print(f"目录中没有 .ykv 文件: {input_dir}")
        return 0

    print(f"找到 {len(ykv_files)} 个 YKV 文件")

    # 输出目录
    out_dir = args.output_dir or os.path.join(input_dir, "out")
    os.makedirs(out_dir, exist_ok=True)

    success = 0
    failed = 0
    # 首个文件成功后缓存的 part1，用于后续文件复用
    cached_part1 = getattr(args, "_cached_part1", "")

    for i, ykv_path in enumerate(ykv_files, 1):
        base = os.path.splitext(os.path.basename(ykv_path))[0]
        out_path = os.path.join(out_dir, f"{base}.mp4")

        # 跳过已存在的输出
        if os.path.exists(out_path):
            print(f"[{i}/{len(ykv_files)}] 跳过（已存在）: {base}")
            success += 1
            continue

        # 把当前缓存 part1 临时装到 args 上，让 process_file 复用
        if cached_part1:
            args._cached_part1 = cached_part1  # noqa: SLF001

        try:
            process_file(
                ykv_path, out_path, ffmpeg_path,
                args.keep_ts, args,
                cached_part1=cached_part1,
            )
            # 提取最新缓存
            cached_part1 = getattr(args, "_cached_part1", cached_part1)
            success += 1
            print(f"  [{i}/{len(ykv_files)}] 完成\n")
        except Exception as e:
            failed += 1
            print(f"  [{i}/{len(ykv_files)}] 失败: {e}\n", file=sys.stderr)

    print(f"\n汇总: 成功 {success}/{len(ykv_files)}, 失败 {failed}")
    return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    # 定位 ffmpeg
    ffmpeg_path = args.ffmpeg or find_ffmpeg()
    if not ffmpeg_path:
        print("错误: 未找到 ffmpeg。请用 --ffmpeg 指定路径，"
              "或将 ffmpeg.exe 放入 PATH。", file=sys.stderr)
        return 1
    print(f"使用 ffmpeg: {ffmpeg_path}")

    # 校验输入存在
    for inp in args.input:
        if not os.path.exists(inp):
            print(f"错误: 文件/目录不存在: {inp}", file=sys.stderr)
            return 1

    if args.batch:
        return process_batch(args, ffmpeg_path)

    # 单/多文件模式
    for input_path in args.input:
        if os.path.isdir(input_path):
            # 误把目录当文件，切回批量
            args.batch = True
            args.input = [input_path]
            return process_batch(args, ffmpeg_path)

    for i, input_path in enumerate(args.input):
        # 自动生成输出路径
        output_path = args.output if len(args.input) == 1 else None
        if output_path is None:
            base = os.path.splitext(os.path.basename(input_path))[0]
            out_dir = args.output_dir or os.path.dirname(input_path)
            output_path = os.path.join(out_dir, f"{base}.mp4")

        try:
            process_file(input_path, output_path, ffmpeg_path,
                         args.keep_ts, args)
        except Exception as e:
            print(f"错误: 处理 {input_path} 失败: {e}", file=sys.stderr)
            if len(args.input) == 1:
                return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
