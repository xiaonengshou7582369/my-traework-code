"""Quick probe: extract segment 1 and run ffprobe/ffmpeg on it directly."""
import os, json, subprocess, sys
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
FFMPEG = r"C:\Users\Administrator\AppData\Roaming\bilibili\ffmpeg\ffmpeg.exe"
FFPROBE = r"C:\Users\Administrator\AppData\Roaming\bilibili\ffmpeg\ffprobe.exe"  # may not exist
YK_HEADER = 34
OUT = Path(r"C:\Users\Administrator\AppData\Local\Temp\ykv_probe")
OUT.mkdir(parents=True, exist_ok=True)

# read manifest
fs = YKV.stat().st_size
with YKV.open("rb") as f:
    f.seek(-16, os.SEEK_END)
    tr = f.read(16).decode("utf-8", "replace")
ml = int(tr.split("\x00",1)[0].strip())
with YKV.open("rb") as f:
    f.seek(-(16+ml), os.SEEK_END)
    raw = f.read(ml)
manifest = json.loads(unquote(raw.decode("utf-8")))
ts = [m for m in manifest if str(m.get("name","")).lower().endswith(".ts")]
ts.sort(key=lambda s: int(s["name"].split(".")[0]))
print(f"Manifest: {len(manifest)} items, {len(ts)} ts segments")
print(f"First seg: name={ts[0]['name']} offset={ts[0]['offset']} size={ts[0]['size']}")

# extract seg 1 (skip YK header)
seg = ts[0]
off = int(seg["offset"]); sz = int(seg["size"])
out1 = OUT / "1.ts"
with YKV.open("rb") as f, out1.open("wb") as w:
    f.seek(off + YK_HEADER)
    rem = sz - YK_HEADER
    while rem > 0:
        c = f.read(min(4*1024*1024, rem))
        if not c: break
        w.write(c); rem -= len(c)
print(f"Wrote {out1} ({out1.stat().st_size} B)")

# Check first bytes
with out1.open("rb") as f:
    head = f.read(8)
print(f"First 8 bytes: {head.hex()}  (sync 0x47? {head[0]==0x47})")

# ffprobe (use ffmpeg -i since no ffprobe)
print("\n=== ffmpeg -i (probe) ===")
r = subprocess.run([FFMPEG, "-hide_banner", "-i", str(out1)], capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stderr[-2000:] if r.stderr else "(no stderr)")
if r.stdout: print("STDOUT:", r.stdout[:500])

# Try ffmpeg copy to mp4
print("\n=== ffmpeg -c copy ===")
mp4 = OUT / "1_copy.mp4"
r2 = subprocess.run([FFMPEG, "-y", "-i", str(out1), "-c", "copy", str(mp4)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace")
print("rc=", r2.returncode)
print(r2.stderr[-1500:] if r2.stderr else "(no stderr)")
if mp4.exists():
    print(f"Output: {mp4.stat().st_size} B")

# Try ffmpeg copy with aac_adtstoasc
print("\n=== ffmpeg -c copy -bsf:a aac_adtstoasc ===")
mp4b = OUT / "1_bsf.mp4"
r3 = subprocess.run([FFMPEG, "-y", "-i", str(out1), "-c", "copy", "-bsf:a", "aac_adtstoasc", str(mp4b)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace")
print("rc=", r3.returncode)
print(r3.stderr[-1500:] if r3.stderr else "(no stderr)")
if mp4b.exists():
    print(f"Output: {mp4b.stat().st_size} B")
