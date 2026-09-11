"""Analyze the DRM module JS to understand the key derivation algorithm."""
import re

js_path = r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js"
with open(js_path, "r", encoding="utf-8") as f:
    js = f.read()

# Search for AES/ECB/encrypt/decrypt patterns
print("=== AES/ECB patterns ===")
for pattern in ["ECB", "AES", "encrypt", "decrypt", "Mode", "padding", "Pkcs7", "NoPadding", "Iso10126"]:
    count = len(re.findall(re.escape(pattern), js, re.IGNORECASE))
    if count > 0:
        print(f"  {pattern}: {count} occurrences")

# Find function definitions - search for "function" keyword followed by names
# The DRM module is minified, so let's look at the structure
# Find the beginning of the module
print("\n=== Module structure (first 2000 chars) ===")
print(js[:2000])

# Find _sce_dlgtqred function definition
# It's likely defined as: _sce_dlgtqred = function(...) { ... }
# or: function _sce_dlgtqred(...) { ... }
print("\n=== Searching for _sce_dlgtqred definition ===")
# Search for assignment patterns
for pattern in [r'_sce_dlgtqred\s*=\s*function', r'function\s+_sce_dlgtqred', r'_sce_dlgtqred\s*[:(]']:
    for m in re.finditer(pattern, js):
        pos = m.start()
        s = max(0, pos - 50)
        e = min(len(js), pos + 500)
        print(f"\n--- pattern '{pattern}' at pos {pos} ---")
        print(js[s:e])

# Search for _sce_r_skjhfnck definition
print("\n=== Searching for _sce_r_skjhfnck definition ===")
for pattern in [r'_sce_r_skjhfnck\s*=\s*function', r'function\s+_sce_r_skjhfnck', r'_sce_r_skjhfnck\s*[:(]']:
    for m in re.finditer(pattern, js):
        pos = m.start()
        s = max(0, pos - 50)
        e = min(len(js), pos + 500)
        print(f"\n--- pattern '{pattern}' at pos {pos} ---")
        print(js[s:e])

# Search for _sce_lgtcaygl definition
print("\n=== Searching for _sce_lgtcaygl definition ===")
for pattern in [r'_sce_lgtcaygl\s*=\s*function', r'function\s+_sce_lgtcaygl', r'_sce_lgtcaygl\s*[:(]']:
    for m in re.finditer(pattern, js):
        pos = m.start()
        s = max(0, pos - 50)
        e = min(len(js), pos + 500)
        print(f"\n--- pattern '{pattern}' at pos {pos} ---")
        print(js[s:e])
