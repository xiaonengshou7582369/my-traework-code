"""Inspect the full configInfo.ups structure for DRM parameters."""
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

# Find the dbInfo entry with configInfo
for m in manifest:
    if "info" in m and isinstance(m["info"], dict):
        ci = m["info"].get("configInfo", {})
        ups = ci.get("ups", {})
        data = ups.get("data", {})
        d = data.get("data", {})

        # Print top-level keys
        print("data.data keys:", list(d.keys()))

        # Print stream[0] full structure
        streams = d.get("stream", [])
        print(f"\nNumber of streams: {len(streams)}")
        if streams:
            s0 = streams[0]
            print(f"\nstream[0] keys: {list(s0.keys())}")
            print(f"stream[0] full:")
            print(json.dumps(s0, ensure_ascii=False, indent=2))

        # Print R1Random and other top-level DRM fields
        print(f"\nR1Random: {ci.get('R1Random')}")
        print(f"encryptR_client: {ci.get('encryptR_client')}")
        print(f"key_index: {ci.get('key_index')}")

        # Search for any field containing "encrypt" or "key" or "R1"
        def find_all(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    p = f"{path}.{k}" if path else k
                    if any(x in k.lower() for x in ["encrypt", "r1", "drm", "key", "copyright"]):
                        print(f"  {p} = {repr(v)[:150]}")
                    if not isinstance(v, (str, int, float, bool)):
                        find_all(v, p)
            elif isinstance(obj, list):
                for i, item in enumerate(obj[:2]):
                    find_all(item, f"{path}[{i}]")
        print("\nAll DRM-related fields:")
        find_all(ci)
        break
