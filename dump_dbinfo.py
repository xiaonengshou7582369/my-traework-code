"""Dump dbInfo entry fully."""
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

# Find dbInfo
for entry in manifest:
    if isinstance(entry, dict) and entry.get("name") == "dbInfo":
        print("=== dbInfo entry ===")
        print("Keys:", list(entry.keys()))
        info = entry.get("info", {})
        print("\ninfo keys:", list(info.keys()) if isinstance(info, dict) else type(info))

        # Dump the full info as pretty JSON
        info_str = json.dumps(info, ensure_ascii=False, indent=2)
        print(f"\nFull info ({len(info_str)} chars):")
        print(info_str[:5000])
        if len(info_str) > 5000:
            print(f"\n... ({len(info_str) - 5000} more chars)")

        # Search for DRM-related keys
        print("\n\n=== Searching for DRM-related keys ===")
        for keyword in ["R1Random", "encryptR", "copyright", "drm", "DRM", "key", "Key", "secret"]:
            if keyword.lower() in info_str.lower():
                idx = info_str.lower().index(keyword.lower())
                print(f"\n  '{keyword}' at pos {idx}:")
                print(f"  ...{info_str[max(0,idx-100):idx+300]}...")
        break

# Also dump the full m3u8
print("\n\n=== Full m3u8 ===")
for entry in manifest:
    if isinstance(entry, dict) and entry.get("name") == "youku.m3u8":
        off = int(entry["offset"]) + YK_HEADER
        size = int(entry["size"]) - YK_HEADER
        with YKV.open("rb") as f:
            f.seek(off)
            m3u8_data = f.read(size)
        content = m3u8_data.decode("utf-8", "replace")
        print(content)
        # Search for key-related directives
        for line in content.split("\n"):
            if "KEY" in line.upper() or "ENCRYPT" in line.upper():
                print(f"\n  *** Found: {line}")
        break
