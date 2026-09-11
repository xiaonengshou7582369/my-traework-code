"""Dump full manifest and m3u8 to find encryption info."""
import os, json
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
YK_HEADER = 34

fs = YKV.stat().st_size
with YKV.open("rb") as f:
    f.seek(-16, os.SEEK_END)
    tr = f.read(16).decode("utf-8", "replace")
ml = int(tr.split("\x00", 1)[0].strip())
with YKV.open("rb") as f:
    f.seek(-(16 + ml), os.SEEK_END)
    raw = f.read(ml)
manifest = json.loads(unquote(raw.decode("utf-8")))

print(f"Manifest has {len(manifest)} entries")
print("\n=== All entry names ===")
for i, entry in enumerate(manifest):
    if isinstance(entry, dict):
        name = entry.get("name", "N/A")
        size = entry.get("size", 0)
        offset = entry.get("offset", 0)
        print(f"  [{i}] {name} offset={offset} size={size}")
        # Print all keys for non-ts entries
        if not name.endswith(".ts"):
            for k, v in entry.items():
                if k not in ["name", "size", "offset"]:
                    vstr = str(v)
                    if len(vstr) > 200:
                        vstr = vstr[:200] + "..."
                    print(f"      {k}: {vstr}")

# Find and dump m3u8
print("\n=== M3U8 Content ===")
for entry in manifest:
    if isinstance(entry, dict) and entry.get("name") == "youku.m3u8":
        off = int(entry["offset"]) + YK_HEADER
        size = int(entry["size"]) - YK_HEADER
        with YKV.open("rb") as f:
            f.seek(off)
            m3u8_data = f.read(size)
        print(m3u8_data.decode("utf-8", "replace"))
        break

# Look for any key-related entries
print("\n=== Key-related entries in manifest ===")
manifest_str = json.dumps(manifest, ensure_ascii=False, indent=2)
for keyword in ["key", "Key", "encrypt", "decrypt", "drm", "DRM", "license", "R1Random", "copyright"]:
    if keyword.lower() in manifest_str.lower():
        idx = manifest_str.lower().index(keyword.lower())
        print(f"\n  '{keyword}' found at pos {idx}:")
        print(f"  ...{manifest_str[max(0,idx-50):idx+200]}...")

# Also check if there are any non-TS, non-m3u8 files
print("\n=== Non-TS, non-m3u8 files ===")
for entry in manifest:
    if isinstance(entry, dict):
        name = entry.get("name", "")
        if not name.endswith(".ts") and name != "youku.m3u8":
            print(f"  {name}")
            off = int(entry["offset"]) + YK_HEADER
            size = int(entry["size"]) - YK_HEADER
            with YKV.open("rb") as f:
                f.seek(off)
                data = f.read(min(size, 1000))
            print(f"    Content (first 500B): {data[:500]}")
