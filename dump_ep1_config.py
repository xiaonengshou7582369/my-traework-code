"""Dump the full config block for episode 1 (vid=XNTk3MzA5NzgzMg==) to find any key/IV field."""
import json
from pathlib import Path

DATA_JSON = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\data.json")
data = json.loads(DATA_JSON.read_text(encoding="utf-8"))

cfg = data["download"]["configs"]
# find episode 1's config
EP1_VID = "XNTk3MzA5NzgzMg=="
ep1 = cfg.get(EP1_VID)
if ep1 is None:
    # show available vids
    print("Available vids:")
    for k in list(cfg.keys())[:10]:
        print(f"  {k}")
    raise SystemExit("EP1 vid not found")

print(f"=== Full config for {EP1_VID} ===\n")
print(json.dumps(ep1, indent=2, ensure_ascii=False)[:10000])
