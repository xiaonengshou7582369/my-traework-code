# Copyright (C) 2026 RainVenturer
# SPDX-License-Identifier: GPL-3.0
"""Command-line interface for YKV-Cracker."""
from __future__ import annotations
import argparse
import os
import sys
from typing import List, Optional

from ykv_cracker import __version__
from ykv_cracker.parser import YKVParser
from ykv_cracker.config_drm import setup_decryption
from ykv_cracker.decryptor import decrypt_ts, decrypt_ts_ecb
from ykv_cracker.key_unwrap import find_part1
from ykv_cracker.converter import ts_segments_to_mp4, find_ffmpeg


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='YKV-Cracker: Decrypt and convert YouKu YKV video files',
    )
    parser.add_argument('input', nargs='+', help='YKV file(s) or directory')
    parser.add_argument('-o', '--output', help='Output MP4 path (single file only)')
    parser.add_argument('-b', '--batch', action='store_true',
                        help='Batch process all .ykv files in input directory')
    parser.add_argument('--ffmpeg', default='ffmpeg',
                        help='Path to ffmpeg executable')
    parser.add_argument('--keep-ts', action='store_true',
                        help='Keep intermediate .ts file')
    # ---- Real DRM pipeline options ----
    key_group = parser.add_mutually_exclusive_group()
    key_group.add_argument('--key-string', metavar='KEY',
                           help='Full key_string "part1,encryptR_server,copyright_key"')
    key_group.add_argument('--part1', metavar='DIGITS',
                           help='6-digit part1; part2/part3 read from YKV JSON trailer')
    key_group.add_argument('--find-part1', action='store_true',
                           help='Brute-force the 6-digit part1 value')
    parser.add_argument('-v', '--version', action='version',
                        version=f'ykv-cracker {__version__}')
    return parser.parse_args(argv)


def _build_key_string(ykv, args: argparse.Namespace) -> str:
    """Construct the ``"part1,encryptR_server,copyright_key"`` string.

    Priority: ``--key-string`` > ``--part1`` + YKV trailer > legacy derive.
    """
    if args.key_string:
        return args.key_string

    encrypt_r = ykv.encryptR_server
    copyright_k = ykv.copyright_key

    if not encrypt_r or not copyright_k:
        raise ValueError(
            "YKV trailer is missing encryptR_server / copyright_key fields. "
            "Use --key-string to provide the full key string directly."
        )

    if args.part1:
        part1 = args.part1
    else:
        raise ValueError(
            "part1 is required. Provide --part1 (6-digit number) or "
            "--key-string (full comma-separated key string)."
        )

    return f"{part1},{encrypt_r},{copyright_k}"


def process_file(
    input_path: str,
    output_path: Optional[str] = None,
    ffmpeg_path: str = 'ffmpeg',
    keep_ts: bool = False,
    args: Optional[argparse.Namespace] = None,
) -> str:
    """Process a single YKV file: decrypt -> convert to MP4."""
    print(f"Processing: {input_path}")

    # Parse YKV
    parser = YKVParser()
    ykv = parser.parse(input_path)
    print(f"  File size: {ykv.file_size:,} bytes ({ykv.file_size/1024/1024:.1f} MB)")
    print(f"  encryptR_server: {ykv.encryptR_server or '(not found)'}")
    print(f"  copyright_key:   {ykv.copyright_key or '(not found)'}")

    # Determine key_string: --find-part1 > --key-string > --part1 + trailer > legacy
    key_string = ''
    use_legacy = False
    decrypted_segments: list[bytes] = []

    if args is not None and getattr(args, 'find_part1', False):
        if not ykv.encryptR_server or not ykv.copyright_key:
            raise ValueError("YKV trailer has no DRM fields, cannot brute-force part1")
        print(f"  Brute-forcing part1...")
        part1 = find_part1(
            ykv.encryptR_server,
            ykv.copyright_key,
            progress_callback=lambda p: print(f'    {p}%', end='\r'),
        )
        if not part1:
            raise ValueError("Could not find valid part1")
        print(f'    Found: part1={part1}')
        key_string = f"{part1},{ykv.encryptR_server},{ykv.copyright_key}"

    elif args is not None and (args.key_string or args.part1):
        key_string = _build_key_string(ykv, args)

    # --- Decrypt with key_string (shared by --find-part1, --key-string, --part1) ---
    if key_string:
        print(f"  Using key_string pipeline (drm_type=2)")
        round_keys = setup_decryption(2, key_string)
        aes_key = round_keys[0]
        total = len(ykv.encrypted_segments)
        for seg in ykv.encrypted_segments:
            decrypted_segments.append(decrypt_ts_ecb(seg, aes_key))
        print(f"  Decrypted {total} segments")

    elif ykv.encryptR_server and ykv.copyright_key and not (args and args.key_string):
        print("  Warning: YKV has encryptR_server + copyright_key but no --part1/--key-string.")
        print("  Falling back to legacy derive_key (this will likely produce garbage).")
        use_legacy = True
    else:
        use_legacy = True

    if use_legacy:
        if ykv.clientR1:
            print(f"  Legacy clientR1: {ykv.clientR1}")
            from ykv_cracker.decryptor import derive_key
            key, iv = derive_key(ykv.clientR1)
            print(f"  AES key: {key.hex()}")
            decrypted_segments = [decrypt_ts_ecb(seg, key) for seg in ykv.encrypted_segments]
        elif ykv.encrypted_segments:
            print("  Warning: No key material found. Trying zero key/IV as last resort...")
            decrypted_segments = [decrypt_ts_ecb(seg, b'\x00' * 16) for seg in ykv.encrypted_segments]
        else:
            raise ValueError("No encrypted data to decrypt")

    # Determine output path
    if not output_path:
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(os.path.dirname(input_path), f"{base}.mp4")

    # Save intermediate TS (concatenated) if keep_ts is True
    if keep_ts:
        ts_path = os.path.splitext(output_path)[0] + '.ts'
        os.makedirs(os.path.dirname(os.path.abspath(ts_path)), exist_ok=True)
        with open(ts_path, 'wb') as f:
            f.write(b''.join(decrypted_segments))
        print(f"  Intermediate TS saved: {ts_path}")

    # Convert to MP4 via ffmpeg concat (preserves per-segment PTS)
    print(f"  Converting {len(decrypted_segments)} segments to MP4: {output_path}")
    result = ts_segments_to_mp4(decrypted_segments, output_path, ffmpeg_path)
    print(f"  Done! Output: {result}")

    return result


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    args = parse_args(argv)

    # Check ffmpeg availability
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        print("Warning: ffmpeg not found on PATH. Install ffmpeg first.", file=sys.stderr)

    if args.batch:
        # Batch mode: process all .ykv files in directory
        input_dir = args.input[0]
        if not os.path.isdir(input_dir):
            print(f"Error: Not a directory: {input_dir}", file=sys.stderr)
            return 1

        ykv_files = sorted([
            os.path.join(input_dir, f)
            for f in os.listdir(input_dir)
            if f.lower().endswith('.ykv')
        ])

        if not ykv_files:
            print(f"No .ykv files found in {input_dir}")
            return 0

        print(f"Found {len(ykv_files)} YKV files to process")
        for i, ykv_path in enumerate(ykv_files, 1):
            try:
                process_file(ykv_path, ffmpeg_path=args.ffmpeg, keep_ts=args.keep_ts, args=args)
                print(f"  [{i}/{len(ykv_files)}] Completed\n")
            except Exception as e:
                print(f"  [{i}/{len(ykv_files)}] FAILED: {e}\n", file=sys.stderr)

    else:
        # Single or multiple files
        for input_path in args.input:
            if not os.path.exists(input_path):
                print(f"Error: File not found: {input_path}", file=sys.stderr)
                return 1

        for i, input_path in enumerate(args.input):
            output_path: Optional[str] = None
            if len(args.input) == 1:
                output_path = args.output
            else:
                # Auto-generate output names for multiple files
                base = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(os.path.dirname(input_path), f"{base}.mp4")

            try:
                process_file(input_path, output_path, args.ffmpeg, args.keep_ts, args=args)
            except Exception as e:
                print(f"Error processing {input_path}: {e}", file=sys.stderr)
                if len(args.input) == 1:
                    return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
