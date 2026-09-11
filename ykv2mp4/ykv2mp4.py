#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ykv2mp4.py - Youku YKV (KLV-packaged MPEG-TS) to MP4 converter.

Toolpack for converting Youku-downloaded .ykv files into standard .mp4 files.

YKV file layout (new KLV-packaged format):
  +------------------------------+-------------------------------+
  | 34-byte YK\\x22\\x00 header   | MPEG-TS payload (188-byte    |
  | per segment (per manifest)   | packets)                      |
  +------------------------------+-------------------------------+
  | ... segments concatenated ...                                |
  +--------------------------------------------------------------+
  | URL-encoded JSON manifest (size_to_skip bytes)               |
  +--------------------------------------------------------------+
  | 16-byte ASCII length trailer (e.g. b"48869\\x00\\x00...")     |
  +--------------------------------------------------------------+

The manifest lists every embedded file (e.g. "1.ts", "2.ts", ...,
"youku.m3u8", "dbInfo") with its offset/size inside the .ykv. Each .ts
segment begins with the 34-byte YK header; skipping it yields a
standard MPEG-TS stream that FFmpeg can concatenate into a single MP4
with `-c copy`.

Usage:
  # Single file
  python ykv2mp4.py "D:\\path\\ep01.ykv" "D:\\out\\ep01.mp4"
  # Batch folder (input folder, output folder)
  python ykv2mp4.py --batch "D:\\in" "D:\\out"
  # Auto-find FFmpeg path
  python ykv2mp4.py --ffmpeg "C:\\bilibili\\ffmpeg.exe" ...

References:
  - https://github.com/zhy8388608/ykv2mp4 (Python prototype, MIT)
  - https://github.com/nhjclxc/ykv2mp4 (Go prototype, source-available)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import unquote

# Constants ----------------------------------------------------------------
YK_HEADER_SIZE = 34          # size of the "YK\\x22\\x00 ..." KLV header per segment
MANIFEST_TRAILER_SIZE = 16   # ASCII length trailer at the very end of the .ykv
TS_PACKET_SIZE = 188         # MPEG-TS packet size (used only for sanity checks)
CHUNK_IO = 4 * 1024 * 1024   # 4 MiB streaming chunk for extraction


# ===========================================================================
# 1. YKV trailer / manifest parsing
# ===========================================================================

def read_manifest(ykv_path: Path) -> list[dict]:
    """Read the URL-encoded JSON manifest from the tail of a .ykv file.

    Returns the list of file-info dicts (each with at least name/offset/size).
    Raises ValueError if the trailer cannot be parsed.
    """
    file_size = ykv_path.stat().st_size
    if file_size < MANIFEST_TRAILER_SIZE + 1:
        raise ValueError(f"File too small to be a YKV: {ykv_path} ({file_size} B)")

    with ykv_path.open("rb") as f:
        f.seek(-MANIFEST_TRAILER_SIZE, os.SEEK_END)
        trailer = f.read(MANIFEST_TRAILER_SIZE)

    # Trailer is ASCII digits terminated by NUL bytes, e.g. b"48869\\x00..."
    trailer_str = trailer.decode("utf-8", errors="replace")
    length_token = trailer_str.split("\x00", 1)[0].strip()
    if not length_token.isdigit():
        raise ValueError(
            f"Cannot parse manifest length from trailer: {trailer!r} "
            f"(decoded: {trailer_str!r})"
        )
    manifest_len = int(length_token)
    if manifest_len <= 0 or manifest_len > file_size:
        raise ValueError(f"Manifest length {manifest_len} out of range for {file_size}B file")

    with ykv_path.open("rb") as f:
        f.seek(-(MANIFEST_TRAILER_SIZE + manifest_len), os.SEEK_END)
        raw_manifest = f.read(manifest_len)

    decoded = unquote(raw_manifest.decode("utf-8"))
    manifest = json.loads(decoded)
    if not isinstance(manifest, list):
        raise ValueError(f"Manifest is not a list, got {type(manifest).__name__}")
    return manifest


def filter_ts_segments(manifest: list[dict]) -> list[dict]:
    """Pick only the .ts segments (skip m3u8, dbInfo, etc.)."""
    segments = [m for m in manifest if str(m.get("name", "")).lower().endswith(".ts")]
    return segments


def segment_index(name: str) -> int:
    """Extract the integer prefix from a name like '1.ts' or '108.ts' for ordering."""
    m = re.match(r"(\d+)", os.path.basename(name))
    return int(m.group(1)) if m else 0


# ===========================================================================
# 2. Segment extraction (streaming)
# ===========================================================================

def extract_segment(
    ykv_path: Path,
    seg: dict,
    out_path: Path,
    skip_yk_header: bool = True,
) -> int:
    """Extract one segment from the .ykv into out_path (streaming, low memory).

    Returns the number of bytes written.
    """
    offset = int(seg["offset"])
    size = int(seg["size"])
    # If skipping the YK header, the payload starts 34 bytes in and is 34 bytes shorter
    payload_start = offset + (YK_HEADER_SIZE if skip_yk_header else 0)
    payload_size = size - (YK_HEADER_SIZE if skip_yk_header else 0)
    if payload_size < 0:
        raise ValueError(f"Segment {seg.get('name')} smaller than YK header: {size}B")

    bytes_written = 0
    with ykv_path.open("rb") as src, out_path.open("wb") as dst:
        src.seek(payload_start)
        remaining = payload_size
        while remaining > 0:
            chunk = src.read(min(CHUNK_IO, remaining))
            if not chunk:
                # Segment declared larger than the bytes actually available
                break
            dst.write(chunk)
            bytes_written += len(chunk)
            remaining -= len(chunk)
    return bytes_written


# ===========================================================================
# 3. FFmpeg merging
# ===========================================================================

def find_ffmpeg(explicit: Optional[str] = None) -> str:
    """Locate an ffmpeg executable."""
    if explicit:
        if Path(explicit).is_file():
            return explicit
        # Maybe they gave a directory
        cand = Path(explicit) / "ffmpeg.exe"
        if cand.is_file():
            return str(cand)
        cand = Path(explicit) / "ffmpeg"
        if cand.is_file():
            return str(cand)
    found = shutil.which("ffmpeg")
    if found:
        return found
    # Common Windows locations
    candidates = [
        r"C:\Users\Administrator\AppData\Roaming\bilibili\ffmpeg\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c
    raise FileNotFoundError(
        "ffmpeg not found. Pass --ffmpeg <path> or add it to PATH."
    )


def build_filelist(segment_paths: list[Path], list_path: Path) -> None:
    """Write the concat demuxer filelist."""
    with list_path.open("w", encoding="utf-8", newline="\n") as f:
        for p in segment_paths:
            # concat demuxer requires forward slashes and single-quote wrapping
            quoted = str(p).replace("\\", "/")
            f.write(f"file '{quoted}'\n")


def _run_ffmpeg(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def merge_segments(
    ffmpeg: str,
    filelist: Path,
    output: Path,
) -> None:
    """Run `ffmpeg -f concat -safe 0 -i filelist -c copy output` with fallbacks."""
    output.parent.mkdir(parents=True, exist_ok=True)

    # Strategy 1: plain -c copy (works for most cases)
    base_cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0",
                "-i", str(filelist), "-c", "copy"]
    rc, out, err = _run_ffmpeg(base_cmd + [str(output)])
    if rc == 0 and output.exists() and output.stat().st_size > 0:
        return

    # Strategy 2: with aac_adtstoasc bitstream filter (TS AAC -> MP4 ASC)
    rc2, out2, err2 = _run_ffmpeg(base_cmd + ["-bsf:a", "aac_adtstoasc", str(output)])
    if rc2 == 0 and output.exists() and output.stat().st_size > 0:
        return

    raise RuntimeError(
        f"ffmpeg merge failed.\n"
        f"  try1 (rc={rc}): {err[-800:]}\n"
        f"  try2 (rc={rc2}): {err2[-800:]}"
    )


# ===========================================================================
# 4. Single-file conversion
# ===========================================================================

def convert_one(
    ykv_path: Path,
    output_path: Path,
    ffmpeg: str,
    work_dir: Path,
    keep_temp: bool = False,
    verbose: bool = False,
) -> None:
    """Convert a single .ykv into .mp4 at output_path."""
    ykv_path = ykv_path.resolve()
    output_path = output_path.resolve()
    start_ts = time.time()

    # Skip if output already exists and is non-trivial
    if output_path.exists() and output_path.stat().st_size > 1024 * 1024:
        print(f"[SKIP] {output_path.name} already exists "
              f"({output_path.stat().st_size/1024/1024:.1f} MiB)")
        return

    print(f"\n[CONVERT] {ykv_path.name}")
    print(f"          size: {ykv_path.stat().st_size/1024/1024:.2f} MiB")

    manifest = read_manifest(ykv_path)
    segments = filter_ts_segments(manifest)
    if not segments:
        raise ValueError(f"No .ts segments found in manifest of {ykv_path.name}")
    segments.sort(key=lambda s: segment_index(s["name"]))
    print(f"          segments: {len(segments)} .ts files "
          f"(1..{segment_index(segments[-1]['name'])})")

    # Per-file temp dir under work_dir, namespaced by ykv stem
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", ykv_path.stem)
    temp_dir = work_dir / f"{safe_stem}_{os.getpid()}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Extract all segments in numeric order
        seg_paths: list[Path] = []
        for i, seg in enumerate(segments, 1):
            seg_name = seg["name"]
            out_seg = temp_dir / seg_name
            t0 = time.time()
            written = extract_segment(ykv_path, seg, out_seg, skip_yk_header=True)
            seg_paths.append(out_seg)
            if verbose or i % 20 == 0 or i == len(segments):
                print(f"          [{i:>3}/{len(segments)}] {seg_name:>10s} "
                      f"{written/1024/1024:6.2f} MiB  ({time.time()-t0:.2f}s)")

        # Build filelist and merge
        filelist = temp_dir / "filelist.txt"
        build_filelist(seg_paths, filelist)
        print(f"          merging {len(seg_paths)} segments with ffmpeg ...")
        merge_segments(ffmpeg, filelist, output_path)

        elapsed = time.time() - start_ts
        out_size = output_path.stat().st_size / 1024 / 1024
        print(f"[OK]      {output_path.name}  {out_size:.2f} MiB  "
              f"in {elapsed:.1f}s")
    finally:
        if not keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)


# ===========================================================================
# 5. Batch conversion
# ===========================================================================

def iter_ykv_files(folder: Path) -> Iterable[Path]:
    """Yield all .ykv files in folder (non-recursive)."""
    for entry in sorted(folder.iterdir()):
        if entry.is_file() and entry.suffix.lower() == ".ykv":
            yield entry


def natural_key(path: Path) -> tuple:
    """Natural sort key: '第2集' < '第10集'."""
    s = path.stem
    return tuple(int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s))


def convert_batch(
    input_folder: Path,
    output_folder: Path,
    ffmpeg: str,
    work_dir: Path,
    keep_temp: bool = False,
    verbose: bool = False,
    limit: Optional[int] = None,
) -> tuple[int, int]:
    """Convert every .ykv under input_folder into output_folder. Returns (ok, fail)."""
    output_folder.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(iter_ykv_files(input_folder), key=natural_key)
    if limit:
        files = files[:limit]
    total = len(files)
    print(f"Found {total} .ykv files in {input_folder}")
    print(f"Output dir: {output_folder}")
    print(f"Work dir:   {work_dir}")
    print(f"FFmpeg:     {ffmpeg}")
    print("=" * 60)

    ok = fail = 0
    batch_start = time.time()
    for idx, ykv in enumerate(files, 1):
        out = output_folder / (ykv.stem + ".mp4")
        print(f"\n========== [{idx}/{total}] ==========")
        try:
            convert_one(ykv, out, ffmpeg, work_dir, keep_temp=keep_temp, verbose=verbose)
            ok += 1
        except Exception as e:
            fail += 1
            print(f"[FAIL]    {ykv.name}: {e}")

    elapsed = time.time() - batch_start
    print("\n" + "=" * 60)
    print(f"Batch done: {ok} ok, {fail} failed, total {total} in {elapsed:.1f}s "
          f"({elapsed/60:.1f} min)")
    return ok, fail


# ===========================================================================
# 6. CLI
# ===========================================================================

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Youku YKV -> MP4 converter (KLV-packaged MPEG-TS variant).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", help="Input .ykv file OR input folder (with --batch)")
    p.add_argument("output", nargs="?", default=None,
                   help="Output .mp4 file (single) or output folder (--batch)")
    p.add_argument("--batch", action="store_true",
                   help="Batch-convert all .ykv files in the input folder")
    p.add_argument("--ffmpeg", default=None,
                   help="Path to ffmpeg.exe or its bin folder (auto-detected if omitted)")
    p.add_argument("--work-dir", default=None,
                   help="Work directory for temp segments (default: system temp)")
    p.add_argument("--keep-temp", action="store_true",
                   help="Keep extracted segment files for inspection")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Print progress for every segment (default: every 20)")
    p.add_argument("--limit", type=int, default=None,
                   help="Batch mode: only process the first N files (for testing)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    try:
        ffmpeg = find_ffmpeg(args.ffmpeg)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    work_dir = Path(args.work_dir) if args.work_dir else Path(tempfile.gettempdir()) / "ykv2mp4_work"

    if args.batch:
        if not args.output:
            print("ERROR: --batch requires an output folder", file=sys.stderr)
            return 2
        ok, fail = convert_batch(
            Path(args.input), Path(args.output), ffmpeg, work_dir,
            keep_temp=args.keep_temp, verbose=args.verbose, limit=args.limit,
        )
        return 0 if fail == 0 else 1

    # Single file
    in_path = Path(args.input)
    if not in_path.is_file():
        print(f"ERROR: input file not found: {in_path}", file=sys.stderr)
        return 2
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = in_path.with_suffix(".mp4")
        # Default to a sibling "mp4" subfolder to avoid clobbering the source
        out_path = in_path.parent / "mp4" / out_path.name
    try:
        convert_one(in_path, out_path, ffmpeg, work_dir,
                    keep_temp=args.keep_temp, verbose=args.verbose)
        return 0
    except Exception as e:
        print(f"[FAIL] {in_path.name}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
