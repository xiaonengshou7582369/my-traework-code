"""Extract and display the embedded m3u8 file from the YKV."""
import os, json
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
YK_HEADER = 34

fs = YKV.stat().st_size
with YKV.open("rb") as f:
    f.seek(-16, os.SEEK_END)
    tr = f.read(16).decode("utf-8", "replace")
lt = tr.split("\x00", 1)[0].strip()
ml = int(lt)
with YKV.open("rb") as f:
    f.seek(-(16 + ml), os.SEEK_END)
    raw = f.read(ml)
manifest = json.loads(unquote(raw.decode("utf-8")))

# Find the m3u8 entry
m3u8_entry = None
for entry in manifest:
    if isinstance(entry, dict) and entry.get("name") == "youku.m3u8":
        m3u8_entry = entry
        break

if m3u8_entry:
    offset = int(m3u8_entry["offset"]) + YK_HEADER
    size = int(m3u8_entry["size"]) - YK_HEADER
    with YKV.open("rb") as f:
        f.seek(offset)
        m3u8_data = f.read(size)
    print("=== Embedded m3u8 ===")
    print(m3u8_data.decode("utf-8", "replace"))
else:
    print("No m3u8 entry found in manifest")

# Also search for R1Random in the entire manifest JSON
manifest_str = json.dumps(manifest, ensure_ascii=False)
print("\n=== Searching for R1Random in manifest ===")
if "R1Random" in manifest_str:
    idx = manifest_str.index("R1Random")
    print(f"Found at position {idx}")
    print(f"Context: ...{manifest_str[max(0,idx-100):idx+200]}...")
else:
    print("R1Random NOT found in manifest")

# Search for "R1" patterns
print("\n=== Searching for R1 fields ===")
for i, entry in enumerate(manifest):
    entry_str = json.dumps(entry, ensure_ascii=False)
    if "R1" in entry_str:
        print(f"Entry [{i}]: contains R1")
        # Find the R1 context
        idx = entry_str.index("R1")
        print(f"  ...{entry_str[max(0,idx-50):idx+100]}...")
