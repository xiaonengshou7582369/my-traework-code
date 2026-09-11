"""Deep-inspect the full manifest of episode 1, especially dbInfo and any key fields."""
import os, json
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")

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
print(f"=== Manifest: {len(m)} entries ===\n")

# Categorize
cats = {}
for e in m:
    name = e.get("name", "?")
    if name.endswith(".ts"):
        cats.setdefault("ts", []).append(e)
    elif name == "dbInfo":
        cats.setdefault("dbInfo", []).append(e)
    elif name.endswith(".m3u8"):
        cats.setdefault("m3u8", []).append(e)
    else:
        cats.setdefault("other", []).append(e)

for k, v in cats.items():
    print(f"  {k}: {len(v)} entries")

# Dump dbInfo in full
print("\n=== dbInfo entry (FULL) ===")
dbi = [e for e in m if e.get("name") == "dbInfo"]
if dbi:
    raw = dbi[0].get("data") or b""
    if isinstance(raw, (bytes, bytearray)):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", "replace")
    else:
        text = raw
    print(f"  size: {len(text)} chars")
    # If it's JSON, pretty print
    try:
        d = json.loads(text)
        print(json.dumps(d, indent=2, ensure_ascii=False)[:8000])
    except Exception as e:
        print(f"  not JSON: {e}")
        print(text[:3000])

# Dump m3u8
print("\n=== m3u8 entries ===")
for e in cats.get("m3u8", []):
    raw = e.get("data") or b""
    if isinstance(raw, (bytes, bytearray)):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", "replace")
    else:
        text = raw
    print(f"  --- {e.get('name')} ({len(text)} chars) ---")
    print(text[:2000])

# Dump first TS segment header only
print("\n=== first TS segment entry fields ===")
ts = cats.get("ts", [])
if ts:
    ts0 = ts[0]
    print(f"  keys: {list(ts0.keys())}")
    for k, v in ts0.items():
        if k == "data":
            print(f"  data: <{len(v)} bytes>")
        else:
            print(f"  {k}: {v!r}")
