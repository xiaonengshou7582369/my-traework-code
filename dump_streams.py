"""Dump the stream array and R1Random specifically for episode 1."""
import json
from pathlib import Path

DATA_JSON = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\data.json")
data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

cfg = data["download"]["configs"]
EP1_VID = "XNTk3MzA5NzgzMg=="
ep1 = cfg[EP1_VID]

# R1Random
print("=== R1Random ===")
print(f"  {ep1.get('R1Random')}")

# streams
streams = ep1["ups"]["data"]["data"]["stream"]
print(f"\n=== {len(streams)} streams ===")
for i, s in enumerate(streams):
    print(f"\n--- stream[{i}] ---")
    # print all keys except large nested ones
    for k, v in s.items():
        if k == "stream_ext":
            # Print stream_ext keys
            print(f"  stream_ext keys: {list(v.keys()) if isinstance(v, dict) else type(v)}")
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    if isinstance(v2, (dict, list)):
                        print(f"    {k2}: <nested {len(v2) if hasattr(v2, '__len__') else '?'}>")
                    else:
                        print(f"    {k2}: {v2}")
        elif isinstance(v, (dict, list)):
            print(f"  {k}: <{type(v).__name__} len={len(v)}>")
        else:
            print(f"  {k}: {v}")

# Look at the full stream_ext of stream[0] in detail
print("\n=== stream[0].stream_ext FULL ===")
se = streams[0].get("stream_ext", {})
for k, v in se.items():
    if isinstance(v, (dict, list)):
        print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:300]}")
    else:
        print(f"  {k}: {v}")

# Also check for any 'key', 'iv', 'kid', 'license' fields anywhere in ep1
print("\n=== All key/iv/kid/license fields in ep1 ===")
def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            if any(t in kl for t in ("key", "iv", "kid", "license", "secret", "salt")):
                p = path + "/" + str(k)
                if isinstance(v, (dict, list)):
                    print(f"  {p}: <{type(v).__name__} len={len(v)}>")
                else:
                    print(f"  {p}: {v}")
            walk(v, path + "/" + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, path + f"[{i}]")
walk(ep1)
