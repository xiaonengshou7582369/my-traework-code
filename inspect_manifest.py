"""Inspect the YKV manifest for DRM parameters."""
import json
import os
from pathlib import Path
from urllib.parse import unquote

ykv = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")

with ykv.open("rb") as f:
    f.seek(-16, os.SEEK_END)
    tr = f.read(16).decode("utf-8", "replace")
lt = tr.split("\x00", 1)[0].strip()
ml = int(lt)
with ykv.open("rb") as f:
    f.seek(-(16 + ml), os.SEEK_END)
    raw = f.read(ml)
manifest = json.loads(unquote(raw.decode("utf-8")))

print(f"Manifest entries: {len(manifest)}")
print(f"Names: {[m.get('name') for m in manifest[:5]]}")

# Dump full manifest as string and search for DRM params
s = json.dumps(manifest, ensure_ascii=False)
print(f"\nFull manifest size: {len(s)} chars")

# Search for DRM-related keys
import re
for pattern in [r'encryptR\w*["\']?\s*[:=]\s*["\']([^"\']+)', 
                r'copyright\w*["\']?\s*[:=]\s*["\']([^"\']+)',
                r'R1Random["\']?\s*[:=]\s*["\']([^"\']+)',
                r'R1random["\']?\s*[:=]\s*["\']([^"\']+)']:
    for m in re.finditer(pattern, s, re.I):
        print(f"  {m.group(0)[:150]}")

# Also look at the dbInfo entry
for m in manifest:
    if "info" in m and isinstance(m["info"], dict):
        ti = m["info"].get("taskInfo", {})
        print(f"\ntaskInfo keys: {list(ti.keys())}")
        # Look for DRM-related fields in the nested structure
        def find_drm(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    p = f"{path}.{k}" if path else k
                    if any(x in k.lower() for x in ["encrypt", "copyright", "r1", "drm", "key"]):
                        print(f"  {p} = {repr(v)[:200]}")
                    find_drm(v, p)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_drm(item, f"{path}[{i}]")
        find_drm(m["info"])
        break
