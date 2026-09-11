"""Dump all DRM-related fields from data.json and YKV dbInfo."""
import json, base64
from pathlib import Path
from urllib.parse import unquote

# 1. Search data.json for ALL DRM-related fields for episode 1
data_path = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\data.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("=" * 70)
print("=== Searching data.json for DRM fields ===")
print("=" * 70)

def deep_search(obj, path="", depth=0):
    """Search for DRM-related keys."""
    if depth > 10:
        return
    drm_keys = ["r1random", "encryptr_server", "copyright_key", "encryptR1",
                "encryptR_server", "encryptr1", "drm_type", "iv", "key_index",
                "clientr1", "serverr2", "drmkey", "encrypt_mode", "encryptr1"]
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if k.lower() in drm_keys or any(dk in k.lower() for dk in drm_keys):
                val_str = str(v)[:100] if not isinstance(v, (dict, list)) else f"({type(v).__name__})"
                print(f"  {p} = {val_str}")
                # Try to base64 decode if it looks like base64
                if isinstance(v, str) and len(v) > 4:
                    try:
                        decoded = base64.b64decode(v)
                        print(f"    b64decode ({len(decoded)}B): {decoded.hex()}")
                    except:
                        pass
            deep_search(v, p, depth + 1)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            deep_search(item, f"{path}[{i}]", depth + 1)

deep_search(data)

# 2. Extract dbInfo from YKV and search for DRM fields
print("\n" + "=" * 70)
print("=== Extracting dbInfo from YKV ===")
print("=" * 70)

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
YK_HEADER = 34

import os
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
dbinfo_entry = None
for entry in manifest:
    if isinstance(entry, dict) and entry.get("name") == "dbInfo":
        dbinfo_entry = entry
        break

if dbinfo_entry:
    off = int(dbinfo_entry["offset"]) + YK_HEADER
    size = int(dbinfo_entry["size"]) - YK_HEADER
    with YKV.open("rb") as f:
        f.seek(off)
        dbinfo_raw = f.read(size)
    try:
        dbinfo = json.loads(unquote(dbinfo_raw.decode("utf-8")))
    except:
        dbinfo = json.loads(dbinfo_raw.decode("utf-8"))

    print(f"dbInfo keys: {list(dbinfo.keys()) if isinstance(dbinfo, dict) else 'not dict'}")

    # Deep search dbInfo for DRM fields
    deep_search(dbinfo, "dbInfo")

    # Also print the stream_ext if it exists
    if isinstance(dbinfo, dict):
        for k in ["stream_ext", "drm", "encryptR_server", "encryptR1", "copyright_key",
                   "R1Random", "drm_type", "iv", "configInfo"]:
            if k in dbinfo:
                print(f"\n  dbInfo.{k} = {json.dumps(dbinfo[k], ensure_ascii=False)[:300]}")

        # Check nested structures
        def find_drm_fields(obj, path="dbInfo", depth=0):
            if depth > 8: return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    p = f"{path}.{k}"
                    if k.lower() in ("r1random", "encrypt_r1", "encryptr1", "encrypt_r_server",
                                     "encryptR_server", "copyright_key", "copyrightkey",
                                     "drm_type", "drmtype", "iv", "key_index", "keyindex",
                                     "encryptmode", "encrypt_mode"):
                        print(f"\n  FOUND: {p} = {json.dumps(v, ensure_ascii=False)[:200]}")
                        if isinstance(v, str) and len(v) > 4:
                            try:
                                decoded = base64.b64decode(v)
                                print(f"    b64decode ({len(decoded)}B): {decoded.hex()}")
                            except:
                                pass
                    find_drm_fields(v, p, depth + 1)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_drm_fields(item, f"{path}[{i}]", depth + 1)

        print("\n=== Deep DRM field search in dbInfo ===")
        find_drm_fields(dbinfo)
else:
    print("dbInfo not found in manifest!")

# 3. Also check m3u8 entries in manifest
print("\n" + "=" * 70)
print("=== Checking m3u8 entries for DRM info ===")
print("=" * 70)
for entry in manifest:
    if isinstance(entry, dict) and "m3u8" in entry.get("name", "").lower():
        off = int(entry["offset"]) + YK_HEADER
        size = int(entry["size"]) - YK_HEADER
        with YKV.open("rb") as f:
            f.seek(off)
            m3u8_raw = f.read(size)
        m3u8_text = unquote(m3u8_raw.decode("utf-8"))
        print(f"\n{entry['name']} ({size}B):")
        print(m3u8_text[:500])
        break
