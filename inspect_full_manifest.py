"""Inspect the full YKV manifest to find all DRM-related parameters."""
import os
import json
import base64
from pathlib import Path
from urllib.parse import unquote

YK_HEADER_SIZE = 34

def read_manifest_full(ykv_path):
    fs = ykv_path.stat().st_size
    with ykv_path.open("rb") as f:
        f.seek(-16, os.SEEK_END)
        tr = f.read(16).decode("utf-8", "replace")
    lt = tr.split("\x00", 1)[0].strip()
    ml = int(lt)
    with ykv_path.open("rb") as f:
        f.seek(-(16 + ml), os.SEEK_END)
        raw = f.read(ml)
    decoded = unquote(raw.decode("utf-8"))
    return json.loads(decoded), raw, decoded

def find_drm_fields(obj, path=""):
    """Recursively find any DRM/encryption-related fields."""
    drm_keys = ["encrypt", "copyright", "r1", "r1random", "key", "drm",
                "license", "aes", "iv", "salt", "secret", "token",
                "cipher", "decrypt", "scramble"]
    results = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = k.lower()
            if any(dk in kl for dk in drm_keys):
                results.append((f"{path}.{k}" if path else k, v))
            if isinstance(v, (dict, list)):
                results.extend(find_drm_fields(v, f"{path}.{k}" if path else k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                results.extend(find_drm_fields(item, f"{path}[{i}]"))
    return results

def main():
    ykv = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
    manifest, raw_manifest, decoded_str = read_manifest_full(ykv)

    print(f"Manifest type: {type(manifest).__name__}")
    print(f"Manifest entries: {len(manifest) if isinstance(manifest, list) else 'N/A'}")
    print(f"Raw manifest length: {len(raw_manifest)} bytes")
    print(f"Decoded manifest length: {len(decoded_str)} chars")

    # Print all entries' names and keys
    if isinstance(manifest, list):
        print("\n=== All manifest entries ===")
        for i, entry in enumerate(manifest):
            if isinstance(entry, dict):
                print(f"[{i}] keys: {list(entry.keys())}")
                print(f"    name: {entry.get('name', 'N/A')}")
                # Print all non-binary values
                for k, v in entry.items():
                    if k != "name" and not isinstance(v, (bytes, bytearray)):
                        val_str = str(v)
                        if len(val_str) > 200:
                            val_str = val_str[:200] + "..."
                        print(f"    {k}: {val_str}")
            else:
                print(f"[{i}] {type(entry).__name__}: {str(entry)[:200]}")

    # Search for DRM-related fields
    print("\n=== DRM-related fields ===")
    drm_fields = find_drm_fields(manifest)
    if drm_fields:
        for path, val in drm_fields:
            val_str = str(val)
            if len(val_str) > 300:
                val_str = val_str[:300] + "..."
            print(f"  {path} = {val_str}")
    else:
        print("  (none found)")

    # Also check the raw manifest for any embedded JSON or keys
    print("\n=== Raw manifest first 500 chars ===")
    print(decoded_str[:500])

    # Check the YK header of the first segment
    print("\n=== YK header of first segment ===")
    if isinstance(manifest, list) and manifest:
        first_seg = manifest[0]
        offset = int(first_seg.get("offset", 0))
        with ykv.open("rb") as f:
            f.seek(offset)
            header = f.read(YK_HEADER_SIZE)
        print(f"Header ({len(header)}B): {header.hex()}")
        print(f"Header ASCII: {header}")
        # Try to decode as strings
        for i in range(len(header)):
            if header[i:i+2] == b"YK":
                print(f"  YK magic at offset {i}")
        # Check for any readable strings
        text_parts = []
        current = b""
        for b in header:
            if 32 <= b < 127:
                current += bytes([b])
            else:
                if len(current) >= 3:
                    text_parts.append(current.decode())
                current = b""
        if current and len(current) >= 3:
            text_parts.append(current.decode())
        print(f"  Readable strings: {text_parts}")

if __name__ == "__main__":
    main()
