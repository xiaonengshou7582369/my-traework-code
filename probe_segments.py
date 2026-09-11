"""Probe the first TS segment from episode 1 to determine if it's actually encrypted."""
import os
import json
import subprocess
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
FFMPEG = r"C:\Users\Administrator\AppData\Roaming\bilibili\ffmpeg\ffmpeg.exe"
YK_HEADER = 34
OUT_DIR = Path(r"c:\Users\Administrator\iCloudDrive\Traework云仓库\6aa2615da516df5d0a1843ba\probe_out")
OUT_DIR.mkdir(exist_ok=True)


def read_manifest(p):
    fs = p.stat().st_size
    with p.open("rb") as f:
        f.seek(-16, os.SEEK_END)
        tr = f.read(16).decode("utf-8", "replace")
    lt = tr.split("\x00", 1)[0].strip()
    ml = int(lt)
    with p.open("rb") as f:
        f.seek(-(16 + ml), os.SEEK_END)
        raw = f.read(ml)
    return json.loads(unquote(raw.decode("utf-8")))


m = read_manifest(YKV)
print(f"Manifest has {len(m)} entries")
for entry in m[:5]:
    print(f"  name={entry.get('name')} offset={entry.get('offset')} size={entry.get('size')}")

ts_segs = [e for e in m if str(e.get("name", "")).lower().endswith(".ts")]
ts_segs.sort(key=lambda s: int(s["name"].split(".")[0]))
print(f"\nFound {len(ts_segs)} TS segments (1..{ts_segs[-1]['name']})")

# Extract segment 1 with and without YK header
seg1 = ts_segs[0]
off = int(seg1["offset"])
size = int(seg1["size"])
print(f"\nSeg1: offset={off} size={size}")

with YKV.open("rb") as f:
    f.seek(off)
    raw_with_header = f.read(size)
with YKV.open("rb") as f:
    f.seek(off + YK_HEADER)
    raw_no_header = f.read(size - YK_HEADER)

# Show first 64 bytes of each
print(f"\nWith YK header (first 64B): {raw_with_header[:64].hex()}")
print(f"  YK header: {raw_with_header[:34]}")
print(f"  TS starts at: {raw_with_header[34:34+4].hex()}")

print(f"\nWithout YK header (first 64B): {raw_no_header[:64].hex()}")
sync_at_0 = raw_no_header[0] == 0x47
sync_at_188 = raw_no_header[188] == 0x47 if len(raw_no_header) > 188 else False
print(f"  0x47 at [0]: {sync_at_0}")
print(f"  0x47 at [188]: {sync_at_188}")

# Save both versions
p_with = OUT_DIR / "seg1_with_header.ts"
p_no = OUT_DIR / "seg1_no_header.ts"
p_with.write_bytes(raw_with_header)
p_no.write_bytes(raw_no_header)
print(f"\nSaved {p_with.name} ({len(raw_with_header)}B) and {p_no.name} ({len(raw_no_header)}B)")

# Probe with FFmpeg
for p in [p_with, p_no]:
    print(f"\n=== ffprobe {p.name} ===")
    r = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(p), "-f", "null", "-"],
        capture_output=True, text=True, errors="replace"
    )
    # Show stderr (ffmpeg prints info there)
    err = r.stderr or ""
    # Just the relevant lines
    for line in err.splitlines():
        if any(k in line.lower() for k in ["stream", "duration", "video:", "audio:", "input", "error", "invalid", "corrupt"]):
            print(f"  {line.strip()}")
    print(f"  rc={r.returncode}")

# Also try probing the whole ykv as input
print(f"\n=== ffprobe entire YKV (first 10MB) ===")
r = subprocess.run(
    [FFMPEG, "-hide_banner", "-i", str(YKV), "-f", "null", "-"],
    capture_output=True, text=True, errors="replace"
)
err = r.stderr or ""
for line in err.splitlines()[:30]:
    print(f"  {line.strip()}")
print(f"  rc={r.returncode}")
