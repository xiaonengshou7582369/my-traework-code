"""Dump the full YKV manifest to see ALL DRM parameters."""
import os, json
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")

fs = YKV.stat().st_size
with YKV.open("rb") as f:
    f.seek(-16, os.SEEK_END)
    tr = f.read(16).decode("utf-8", "replace")
lt = tr.split("\x00", 1)[0].strip()
ml = int(lt)
print(f"File size: {fs}")
print(f"Trailer: {tr!r}")
print(f"Manifest length: {ml}")

with YKV.open("rb") as f:
    f.seek(-(16 + ml), os.SEEK_END)
    raw = f.read(ml)

manifest = json.loads(unquote(raw.decode("utf-8")))
print(f"\nManifest entries: {len(manifest)}")

# Show all entries
for i, entry in enumerate(manifest):
    if isinstance(entry, dict):
        name = entry.get("name", "?")
        if name.endswith(".ts"):
            if i < 3 or i >= len(manifest) - 3:
                print(f"  [{i}] {entry}")
            elif i == 3:
                print(f"  ... ({len(manifest) - 6} more TS segments) ...")
        else:
            print(f"  [{i}] {entry}")
    else:
        print(f"  [{i}] (type={type(entry).__name__}) {entry}")
