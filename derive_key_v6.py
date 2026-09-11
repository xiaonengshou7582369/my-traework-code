"""Patch the JS code to fix UTF-8 conversion and derive the correct key."""
import json
import base64
from pathlib import Path
from py_mini_racer import MiniRacer

R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7j7M+vQc="

JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")


def main():
    js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")

    # Patch the UTF8 stringify function to bypass UTF-8 conversion
    # Original: stringify:function(r){try{return decodeURIComponent(escape(f.stringify(r)))}catch(r){throw new Error("d42hksldla")}}
    # Patched: return f.stringify(r) directly (Latin1 string)
    old_pattern = 'decodeURIComponent(escape(f.stringify(r)))'
    new_pattern = 'f.stringify(r)'

    if old_pattern in js_code:
        print(f"Found pattern at position {js_code.find(old_pattern)}")
        js_code_patched = js_code.replace(old_pattern, new_pattern)
        print("Patched successfully!")
    else:
        print("Pattern not found, trying alternative search...")
        # Search for the exact error string
        err_pattern = 'throw new Error("d42hksldla")'
        if err_pattern in js_code:
            print(f"Found error pattern at {js_code.find(err_pattern)}")
            # Get surrounding context
            idx = js_code.find(err_pattern)
            start = max(0, idx - 200)
            print(f"Context: ...{js_code[start:idx+100]}...")
        return

    ctx = MiniRacer()

    setup_js = r"""
    var window = this;
    var self = this;
    var global = this;
    var navigator = { userAgent: 'Mozilla/5.0', platform: 'Win32', language: 'zh-CN' };
    var document = {
        createElement: function() { return { setAttribute: function(){}, appendChild: function(){}, style: {}, getContext: function(){ return null; }, addEventListener: function(){} }; },
        getElementsByTagName: function() { return [{ appendChild: function(){}, addEventListener: function(){} }]; },
        getElementById: function() { return null; },
        body: { appendChild: function(){}, addEventListener: function(){} },
        head: { appendChild: function(){} },
        addEventListener: function(){}, removeEventListener: function(){},
        cookie: '', referrer: '', title: '', URL: 'https://www.youku.com/', domain: 'youku.com'
    };
    var location = { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:', pathname: '/', search: '', hash: '' };
    var localStorage = { getItem: function(){ return null; }, setItem: function(){}, removeItem: function(){} };
    var sessionStorage = { getItem: function(){ return null; }, setItem: function(){}, removeItem: function(){} };
    var performance = { now: function(){ return Date.now(); }, timing: { navigationStart: 0 } };
    var console = { log: function(){}, error: function(){}, warn: function(){}, debug: function(){}, info: function(){} };
    """
    ctx.eval(setup_js)

    # Load patched JS
    ctx.eval(js_code_patched)
    print("Patched JS loaded!")

    # Call _sce_dlgtqred multiple times to check determinism
    for run in range(3):
        code = "(function() {" \
            "var key = _sce_dlgtqred('" + R1_RANDOM + "', '" + ENCRYPTR_SERVER + "', '" + COPYRIGHT_KEY + "');" \
            "var info = { type: typeof key, hex: '', length: 0 };" \
            "if (typeof key === 'string') {" \
            "  info.length = key.length;" \
            "  for (var i = 0; i < key.length; i++) {" \
            "    info.hex += key.charCodeAt(i).toString(16).padStart(2, '0');" \
            "  }" \
            "} else if (Array.isArray(key)) {" \
            "  info.length = key.length;" \
            "  for (var i = 0; i < key.length; i++) {" \
            "    info.hex += (key[i] & 0xFF).toString(16).padStart(2, '0');" \
            "  }" \
            "}" \
            "try { info.toString = key.toString(); } catch(e) { info.toString = 'err'; }" \
            "return JSON.stringify(info);" \
            "})();"

        result = ctx.eval(code)
        info = json.loads(result)
        print(f"\nRun {run+1}:")
        print(f"  type: {info['type']}")
        print(f"  length: {info['length']}")
        print(f"  hex: {info['hex']}")

    # Also call _sce_lgtcaygl for comparison
    code2 = "(function() {" \
        "var key = _sce_lgtcaygl('" + R1_RANDOM + "', '" + ENCRYPTR_SERVER + "', '" + COPYRIGHT_KEY + "');" \
        "return JSON.stringify({ type: typeof key, value: key });" \
        "})();"
    result2 = ctx.eval(code2)
    info2 = json.loads(result2)
    print(f"\n_sce_lgtcaygl: type={info2['type']}, value={info2.get('value')}")

    # Try to use the key from _sce_dlgtqred for decryption
    print("\n=== Testing key from _sce_dlgtqred for AES decryption ===")
    key_hex = info['hex']
    if len(key_hex) >= 32:  # at least 16 bytes
        key_bytes = bytes.fromhex(key_hex)
        print(f"Key bytes ({len(key_bytes)}B): {key_hex}")

        # Test on PES payload
        import os
        import sys
        from urllib.parse import unquote
        from Crypto.Cipher import AES

        ykv_path = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
        YK_HEADER_SIZE = 34
        VIDEO_PID = 0x0100

        fs = ykv_path.stat().st_size
        with ykv_path.open("rb") as f:
            f.seek(-16, os.SEEK_END)
            tr = f.read(16).decode("utf-8", "replace")
        lt = tr.split("\x00", 1)[0].strip()
        ml = int(lt)
        with ykv_path.open("rb") as f:
            f.seek(-(16 + ml), os.SEEK_END)
            raw = f.read(ml)
        manifest = json.loads(unquote(raw.decode("utf-8")))

        ts_segs = [m for m in manifest if str(m.get("name", "")).lower().endswith(".ts")]
        ts_segs.sort(key=lambda s: int(s["name"].split(".")[0]))
        seg = ts_segs[0]
        offset = int(seg["offset"])
        size = int(seg["size"])
        with ykv_path.open("rb") as f:
            f.seek(offset + YK_HEADER_SIZE)
            data = f.read(size - YK_HEADER_SIZE)

        # Get first video PES payload
        n_packets = len(data) // 188
        for i in range(n_packets):
            pkt = data[i * 188: (i + 1) * 188]
            if pkt[0] != 0x47:
                continue
            pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
            pusi = (pkt[1] >> 6) & 1
            if pid == VIDEO_PID and pusi == 1:
                afc = (pkt[3] >> 4) & 0x3
                payload_start = 4
                if afc in (2, 3):
                    af_len = pkt[4]
                    payload_start = 5 + af_len
                pes = pkt[payload_start:]
                if pes[:3] == b"\x00\x00\x01":
                    hdr_data_len = pes[8]
                    payload_offset = 9 + hdr_data_len
                    pes_payload = pes[payload_offset:]
                    while pes_payload and pes_payload[-1] == 0xFF:
                        pes_payload = pes_payload[:-1]

                    print(f"PES payload: {len(pes_payload)}B, first 16B: {pes_payload[:16].hex()}")

                    # Try decryption with different key sizes
                    for key_len, label in [(16, "first 16"), (24, "first 24"), (32, "all 32")]:
                        if len(key_bytes) >= key_len:
                            k = key_bytes[:key_len]
                            n = (len(pes_payload) // 16) * 16
                            if n > 0:
                                dec = AES.new(k, AES.MODE_ECB).decrypt(pes_payload[:n])
                                nal4 = dec.count(b"\x00\x00\x00\x01")
                                nal3 = dec.count(b"\x00\x00\x01")
                                flag = "***" if nal4 > 0 or nal3 > 0 else "   "
                                print(f"  {flag} {label}B ECB: nal4={nal4} nal3={nal3} first16={dec[:16].hex()}")
                    break


if __name__ == "__main__":
    main()
