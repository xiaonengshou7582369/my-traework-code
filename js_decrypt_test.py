"""Use Youku's own JS to decrypt the PES payload - the exact same code path as the player."""
import json
import os
import base64
from pathlib import Path
from urllib.parse import unquote
from py_mini_racer import MiniRacer

R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc="

# Use the 9bfde... file which has the clean module structure
JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\9bfde36f7528f854b52055218f494ec0.js")

YK_HEADER_SIZE = 34
VIDEO_PID = 0x0100


def read_manifest(ykv_path):
    with ykv_path.open("rb") as f:
        f.seek(-16, os.SEEK_END)
        tr = f.read(16).decode("utf-8", "replace")
    lt = tr.split("\x00", 1)[0].strip()
    ml = int(lt)
    with ykv_path.open("rb") as f:
        f.seek(-(16 + ml), os.SEEK_END)
        raw = f.read(ml)
    return json.loads(unquote(raw.decode("utf-8")))


def get_first_video_pes(ykv_path):
    manifest = read_manifest(ykv_path)
    ts_segs = [m for m in manifest if str(m.get("name", "")).lower().endswith(".ts")]
    ts_segs.sort(key=lambda s: int(s["name"].split(".")[0]))
    seg = ts_segs[0]
    offset = int(seg["offset"])
    size = int(seg["size"])
    with ykv_path.open("rb") as f:
        f.seek(offset + YK_HEADER_SIZE)
        data = f.read(size - YK_HEADER_SIZE)

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
                return pes_payload, data
    return b"", data


def main():
    ykv = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
    pes_payload, ts_data = get_first_video_pes(ykv)
    print(f"PES payload: {len(pes_payload)}B, first16: {pes_payload[:16].hex()}")

    # Convert PES payload to hex string for JS
    pes_hex = pes_payload.hex()

    js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")

    # Patch the UTF8 stringify to bypass error
    old_pattern = 'decodeURIComponent(escape(f.stringify(r)))'
    new_pattern = 'f.stringify(r)'
    if old_pattern in js_code:
        js_code = js_code.replace(old_pattern, new_pattern)
        print("Patched UTF8 stringify.")
    else:
        print("WARNING: Patch pattern not found!")

    ctx = MiniRacer()

    # Setup browser-like environment
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
    print("Loading JS...")
    ctx.eval(js_code)
    print("JS loaded!")

    # Now use the JS to:
    # 1. Call _sce_dlgtqred to get the key
    # 2. Find the AES class (s) and create an instance with the key
    # 3. Decrypt the PES payload

    # The AES class is internal to the module, not exposed globally.
    # But decryptAES128ECB IS accessible via the module system.
    # Let's try to find a way to access the decryption function.

    # Actually, the simplest approach: just call _sce_dlgtqred and then
    # manually do AES-ECB in Python, trying different key interpretations.

    # First, let's get the raw key from _sce_dlgtqred
    code = """
    (function() {
        try {
            var key = _sce_dlgtqred('""" + R1_RANDOM + """', '""" + ENCRYPTR_SERVER + """', '""" + COPYRIGHT_KEY + """');
            var info = {
                type: typeof key,
                length: key ? key.length : -1,
                hex: '',
                charCodes: []
            };
            if (key) {
                if (key.length !== undefined) {
                    for (var i = 0; i < key.length; i++) {
                        var v;
                        if (typeof key[i] === 'number') v = key[i];
                        else if (typeof key[i] === 'string') v = key[i].charCodeAt(0);
                        else v = -1;
                        info.charCodes.push(v);
                        if (v >= 0) info.hex += (v & 0xFF).toString(16).padStart(2, '0');
                    }
                }
                if (typeof key === 'string') {
                    info.strLength = key.length;
                    info.strHex = '';
                    for (var j = 0; j < key.length; j++) {
                        info.strHex += key.charCodeAt(j).toString(16).padStart(2, '0');
                    }
                }
            }
            return JSON.stringify(info);
        } catch(e) {
            return JSON.stringify({error: e.message, stack: e.stack ? e.stack.substring(0, 500) : ''});
        }
    })();
    """
    result = ctx.eval(code)
    info = json.loads(result)
    print(f"\n_sce_dlgtqred result:")
    print(json.dumps(info, indent=2))

    # Now let's try to find and call the internal AES decrypt directly in JS
    # The key insight: we need to find the AES class constructor and call it
    # Let's try to hook into the module system

    # Actually, let's try a different approach: patch the JS to expose the
    # decryptAES128ECB function globally
    expose_code = r"""
    // Try to find the decrypt function by hooking into the module system
    // The module at pos 516721 has: t.decrypt = function(e, t, i) { if ("AES-ECB" === e.name) return n.decryptAES128ECB(t, i); ... }
    // Let's try to expose it by creating a fake context

    // Actually, let's just try to create the AES class directly
    // The AES class 's' has: coerceArray, createArray, _prepare, decrypt
    // We can find it by looking for the pattern

    // Let's try to use the internal module system
    try {
        // The webpack module system: modules are stored in an array
        // We need to find the module that exports the AES class

        // Alternative: just reconstruct the AES decryption in JS
        // We know the AES class takes a key, coerces it, and calls _prepare
        // _prepare does the AES key schedule

        // Let's try to call decryptAES128ECB by creating a minimal AES implementation
        // that matches what Youku's code does

        // Actually, the simplest approach: the key from _sce_dlgtqred is 18 bytes.
        // coerceArray converts it to Uint8Array(18).
        // _prepare() does the AES key schedule.
        // But standard AES needs 16/24/32 bytes.
        // Maybe _prepare truncates to 16? Let's test with first 16 bytes.
    } catch(e) {
        return JSON.stringify({error: e.message});
    }
    """

    # Let's try the most likely interpretation: key is first 16 bytes of the 18-byte result
    if info.get('hex'):
        key_hex = info['hex']
        key_bytes = bytes.fromhex(key_hex)
        print(f"\nKey bytes ({len(key_bytes)}B): {key_hex}")

        # Try different key lengths
        from Crypto.Cipher import AES

        for klen, label in [(16, "first16"), (24, "first24")]:
            if len(key_bytes) >= klen:
                k = key_bytes[:klen]
                n = (len(pes_payload) // 16) * 16
                if n > 0:
                    try:
                        dec = AES.new(k, AES.MODE_ECB).decrypt(pes_payload[:n])
                        nal4 = dec.count(b"\x00\x00\x00\x01")
                        nal3 = dec.count(b"\x00\x00\x01")
                        flag = "***" if nal4 > 0 or nal3 > 0 else "   "
                        print(f"  {flag} {label}B ECB: nal4={nal4} nal3={nal3} first16={dec[:16].hex()}")
                    except Exception as e:
                        print(f"  {label}B ECB error: {e}")

        # Also try: maybe the key needs to be the UTF-8 converted string
        if info.get('strHex'):
            str_key = bytes.fromhex(info['strHex'])
            print(f"\nString key ({len(str_key)}B): {info['strHex']}")
            for klen, label in [(16, "str_first16"), (24, "str_first24")]:
                if len(str_key) >= klen:
                    k = str_key[:klen]
                    n = (len(pes_payload) // 16) * 16
                    if n > 0:
                        try:
                            dec = AES.new(k, AES.MODE_ECB).decrypt(pes_payload[:n])
                            nal4 = dec.count(b"\x00\x00\x00\x01")
                            nal3 = dec.count(b"\x00\x00\x01")
                            flag = "***" if nal4 > 0 or nal3 > 0 else "   "
                            print(f"  {flag} {label}B ECB: nal4={nal4} nal3={nal3} first16={dec[:16].hex()}")
                        except Exception as e:
                            print(f"  {label}B ECB error: {e}")

    # Now try the BIG approach: use the JS AES implementation directly
    # by evaluating the relevant JS code
    print("\n=== Trying JS-based AES decryption ===")
    try:
        # Extract just the AES class and decryption code from the JS
        # The AES class is the 's' variable in the module
        # Let's try to call it through the module system

        # Actually, let's try to find __webpack_require__ and call the decrypt module
        js_decrypt_code = """
        (function() {
            try {
                // Try to access webpack modules
                if (typeof __webpack_modules__ !== 'undefined') {
                    return 'webpack_modules found';
                }
                if (typeof __webpack_require__ !== 'undefined') {
                    return 'webpack_require found';
                }

                // Try to find the decrypt module by searching for decryptAES128ECB
                var found = false;
                for (var key in this) {
                    if (typeof this[key] === 'object' && this[key]) {
                        for (var k2 in this[key]) {
                            if (k2 === 'decryptAES128ECB' || k2 === 'decrypt') {
                                return 'found: ' + key + '.' + k2;
                            }
                        }
                    }
                }
                return 'nothing found, keys: ' + Object.keys(this).join(',').substring(0, 200);
            } catch(e) {
                return 'error: ' + e.message;
            }
        })();
        """
        result2 = ctx.eval(js_decrypt_code)
        print(f"  JS search result: {result2}")
    except Exception as e:
        print(f"  JS search error: {e}")


if __name__ == "__main__":
    main()
