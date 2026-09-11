# Copyright (C) 2026 RainVenturer
# SPDX-License-Identifier: GPL-3.0
"""FFmpeg-based TS to MP4 converter."""
from __future__ import annotations
import subprocess
import os
import shutil
import tempfile
from typing import Optional

TS_PACKET_SIZE = 188


GPU_AVAILABLE = False  # Phase 2


def find_ffmpeg() -> Optional[str]:
    """Locate ffmpeg binary on the system."""
    ffmpeg = shutil.which('ffmpeg')
    if ffmpeg:
        return ffmpeg

    # Common Windows paths
    windows_paths = [
        r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
        r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
    ]
    for path in windows_paths:
        if os.path.exists(path):
            return path

    return None


def ts_to_mp4(
    ts_data: bytes,
    output_path: str,
    ffmpeg_path: str = 'ffmpeg',
    progress_callback=None,
) -> str:
    """
    Convert single TS blob to MP4 using ffmpeg.

    Writes TS data to a temp file, runs ffmpeg remux, returns output path.
    Prefer :func:`ts_segments_to_mp4` when working with multi-segment YKV files,
    because each segment has its own PTS timeline starting from 0 — raw
    concatenation corrupts frame ordering.
    """
    return ts_segments_to_mp4([ts_data], output_path, ffmpeg_path, progress_callback)


def ts_segments_to_mp4(
    segments: list[bytes],
    output_path: str,
    ffmpeg_path: str = 'ffmpeg',
    progress_callback=None,
) -> str:
    """
    Convert multiple TS segments to MP4 using ffmpeg's concat demuxer.

    Each YKV segment has its own PTS timeline starting from 0.  Raw
    concatenation mixes up frame order; the concat demuxer adjusts
    PTS values so playback is sequential.

    Args:
        segments: List of TS data blobs (each is a valid short TS stream).
        output_path: Destination MP4 path.
        ffmpeg_path: Path to ffmpeg executable.
        progress_callback: Optional callback (not used currently).

    Returns:
        ``output_path`` on success.

    Raises:
        ValueError: If no valid sync bytes found.
        RuntimeError: If ffmpeg fails.
    """
    if not segments:
        raise ValueError("No segments to convert")

    # Validate each segment has sync bytes
    for i, seg in enumerate(segments):
        if len(seg) > 0 and seg[0] != 0x47:
            raise ValueError(f"Segment {i}: first byte is not a TS sync byte")

    temp_dir = tempfile.mkdtemp(prefix='ykv_')
    concat_file = os.path.join(temp_dir, 'concat.txt')
    temp_files = []

    try:
        # Write each segment to a temp file
        for i, seg in enumerate(segments):
            ts_path = os.path.join(temp_dir, f'{i:04d}.ts')
            with open(ts_path, 'wb') as f:
                f.write(seg)
            temp_files.append(ts_path)

        # Create concat file (use safe format for ffmpeg)
        with open(concat_file, 'w', encoding='utf-8') as f:
            for ts_path in temp_files:
                escaped = ts_path.replace("'", "'\\''")
                f.write(f"file '{escaped}'\n")

        cmd = [
            ffmpeg_path,
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            '-movflags', '+faststart',
            output_path,
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=False,
        )

        if proc.returncode != 0:
            stderr_text = ''
            if proc.stderr:
                stderr_text = proc.stderr.decode('utf-8', errors='replace')[:500]
            raise RuntimeError(
                f"ffmpeg failed (exit {proc.returncode}):\n"
                f"{stderr_text}"
            )

        if not os.path.exists(output_path):
            raise RuntimeError(f"Output file not created: {output_path}")

        return output_path

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def check_gpu_support(ffmpeg_path: str = 'ffmpeg') -> dict:
    """Detect available GPU encoders. Returns dict of encoder_name -> available."""
    result = {}
    encoders = {
        'h264_nvenc': 'NVIDIA NVENC',
        'h264_amf': 'AMD AMF',
        'h264_qsv': 'Intel QSV',
        'h264_videotoolbox': 'Apple VideoToolbox',
    }

    try:
        info = subprocess.run(
            [ffmpeg_path, '-encoders'],
            capture_output=True, text=False,
        )
        for enc, name in encoders.items():
            stdout = info.stdout.decode('utf-8', errors='replace') if info.stdout else ''
            result[name] = enc in stdout
    except FileNotFoundError:
        pass

    return result
