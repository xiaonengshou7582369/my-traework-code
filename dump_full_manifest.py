"""Dump full manifest from YKV, especially dbInfo with DRM params."""
import os, json
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
YK_HEADER = 34

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
print(f"Total manifest entries: {len(m)}")

# Print all non-TS entries with full detail
for e in m:
    if not (isinstance(e, dict) and e.get("name", "").endswith(".ts")):
        print(f"\n=== {e.get('name', 'unknown')} ===")
        print(json.dumps(e, indent=2, ensure_ascii=False)[:2000])

# Check first few TS segments for any DRM info
ts = [e for e in m if isinstance(e, dict) and e.get("name", "").endswith(".ts")]
print(f"\n\n=== First 3 TS segments ===")
for s in ts[:3]:
    print(json.dumps(s, indent=2, ensure_ascii=False))

# Check if m3u8 entry has DRM info
m3u8 = [e for e in m if isinstance(e, dict) and "m3u8" in e.get("name", "")]
if m3u8:
    print(f"\n=== m3u8 entry ===")
    # Read the m3u8 content
    for entry in m3u8:
        off = int(entry["offset"]) + YK_HEADER
        size = int(entry["size"]) - YK_HEADER if "size" in entry else int(entry.get("size", 0))
        # Actually, let's just read the raw m3u8 content
        off = int(entry["offset"])
        size = int(entry["size"])
        with YKV.open("rb") as f:
            f.seek(off + YK_HEADER)
            data = f.read(size - YK_HEADER)
        try:
            text = data.decode("utf-8", "replace")
            print(f"m3u8 content (first 3000 chars):")
            print(text[:3000])
        except:
            print(f"m3u8 raw (first 200 hex): {data[:200].hex()}")
