"""Deep inspection of _sce_dlgtqred return value."""
import json
import base64
from pathlib import Path
from py_mini_racer import MiniRacer
from Crypto.Cipher import AES

R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc="

JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")


def main():
    js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")
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

    var escape = function(str) {
        var result = '';
        for (var i = 0; i < str.length; i++) {
            var c = str.charCodeAt(i);
            if (c > 127) { result += '%' + c.toString(16).toUpperCase().padStart(2, '0'); }
            else if (c < 32 || c == 37 || c == 43 || c == 61 || c == 91 || c == 93 || c == 123 || c == 125 || c == 124 || c == 92 || c == 94 || c == 126 || c == 96 || c == 39 || c == 34) { result += '%' + c.toString(16).toUpperCase().padStart(2, '0'); }
            else { result += str.charAt(i); }
        }
        return result;
    };
    var decodeURIComponent = function(str) {
        var bytes = [];
        var i = 0;
        while (i < str.length) {
            if (str[i] == '%' && i + 2 < str.length) { bytes.push(parseInt(str.substr(i+1, 2), 16)); i += 3; }
            else { bytes.push(str.charCodeAt(i)); i++; }
        }
        var result = '';
        var j = 0;
        while (j < bytes.length) {
            var b = bytes[j];
            if (b < 128) { result += String.fromCharCode(b); j++; }
            else if (b >= 192 && b < 224 && j + 1 < bytes.length) { result += String.fromCharCode(((b & 31) << 6) | (bytes[j+1] & 63)); j += 2; }
            else if (b >= 224 && b < 240 && j + 2 < bytes.length) { result += String.fromCharCode(((b & 15) << 12) | ((bytes[j+1] & 63) << 6) | (bytes[j+2] & 63)); j += 3; }
            else if (b >= 240 && j + 3 < bytes.length) { var cp = ((b & 7) << 18) | ((bytes[j+1] & 63) << 12) | ((bytes[j+2] & 63) << 6) | (bytes[j+3] & 63); cp -= 0x10000; result += String.fromCharCode(0xD800 + (cp >> 10)) + String.fromCharCode(0xDC00 + (cp & 0x3FF)); j += 4; }
            else { result += String.fromCharCode(b); j++; }
        }
        return result;
    };
    var encodeURIComponent = function(str) { return str; };
    var atob = function(s) {
        var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
        var str = s.replace(/=+$/, '');
        var result = '';
        for (var i = 0; i < str.length; i += 4) {
            var n = (chars.indexOf(str[i]) << 18) | (chars.indexOf(str[i+1]) << 12) | (i+2 < str.length ? chars.indexOf(str[i+2]) << 6 : 0) | (i+3 < str.length ? chars.indexOf(str[i+3]) : 0);
            result += String.fromCharCode((n >> 16) & 255);
            if (i+2 < str.length && str[i+2] != '=') result += String.fromCharCode((n >> 8) & 255);
            if (i+3 < str.length && str[i+3] != '=') result += String.fromCharCode(n & 255);
        }
        return result;
    };
    var btoa = function(s) {
        var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
        var result = '';
        for (var i = 0; i < s.length; i += 3) {
            var n = (s.charCodeAt(i) << 16) | (i+1 < s.length ? s.charCodeAt(i+1) << 8 : 0) | (i+2 < s.length ? s.charCodeAt(i+2) : 0);
            result += chars[(n >> 18) & 63];
            result += chars[(n >> 12) & 63];
            result += i+1 < s.length ? chars[(n >> 6) & 63] : '=';
            result += i+2 < s.length ? chars[n & 63] : '=';
        }
        return result;
    };
    var console = { log: function(){}, error: function(){}, warn: function(){}, debug: function(){}, info: function(){} };
    """

    ctx.eval(setup_js)
    ctx.eval(js_code)
    print("JS loaded.")

    # Deep inspection of _sce_dlgtqred return value
    code = """
    (function() {
        try {
            var r = _sce_dlgtqred('""" + R1_RANDOM + """', '""" + ENCRYPTR_SERVER + """', '""" + COPYRIGHT_KEY + """');
            var info = {
                typeof: typeof r,
                constructor: r && r.constructor ? r.constructor.name : 'unknown',
                length: r && r.length !== undefined ? r.length : -1,
                byteLength: r && r.byteLength !== undefined ? r.byteLength : -1,
                bufferByteLength: (r && r.buffer && r.buffer.byteLength !== undefined) ? r.buffer.byteLength : -1,
                keys: r ? Object.keys(r).join(',') : '',
                toString: r ? r.toString().substring(0, 200) : '',
                hex: '',
                allValues: []
            };

            // Try to extract bytes in multiple ways
            if (r) {
                // Method 1: iterate as array
                if (r.length !== undefined) {
                    for (var i = 0; i < r.length; i++) {
                        var v = r[i];
                        if (typeof v === 'number') {
                            info.allValues.push(v);
                            info.hex += (v & 0xFF).toString(16).padStart(2, '0');
                        } else if (typeof v === 'string') {
                            info.allValues.push(v.charCodeAt(0));
                            info.hex += (v.charCodeAt(0) & 0xFF).toString(16).padStart(2, '0');
                        }
                    }
                }

                // Method 2: if it has a buffer (Uint8Array)
                if (r.buffer && r.buffer.byteLength !== undefined) {
                    info.bufferHex = '';
                    var view = new Uint8Array(r.buffer);
                    for (var j = 0; j < view.length; j++) {
                        info.bufferHex += view[j].toString(16).padStart(2, '0');
                    }
                    info.bufferLength = view.length;
                }
            }
            return JSON.stringify(info);
        } catch(e) {
            return JSON.stringify({error: e.message, stack: e.stack ? e.stack.substring(0, 1000) : ''});
        }
    })();
    """

    result = ctx.eval(code)
    info = json.loads(result)
    print("\n_sce_dlgtqred deep inspection:")
    print(json.dumps(info, indent=2))

    # Now try to use the key for decryption
    if info.get('hex'):
        key_hex = info['hex']
        key_bytes = bytes.fromhex(key_hex)
        print(f"\nKey bytes ({len(key_bytes)}B): {key_hex}")

        # Also check buffer hex if available
        if info.get('bufferHex'):
            buf_hex = info['bufferHex']
            buf_bytes = bytes.fromhex(buf_hex)
            print(f"Buffer bytes ({len(buf_bytes)}B): {buf_hex}")

        # Try all 16-byte windows from the key
        for i in range(len(key_bytes) - 15):
            k = key_bytes[i:i+16]
            test_decryption(k, f"key[{i}:{i+16}]")

        # Also try buffer bytes
        if info.get('bufferHex'):
            buf_bytes = bytes.fromhex(info['bufferHex'])
            for i in range(len(buf_bytes) - 15):
                k = buf_bytes[i:i+16]
                test_decryption(k, f"buf[{i}:{i+16}]")

        # Try with decodeKey approach: coerceArray might pad/truncate
        # If the key is 14 bytes, maybe pad to 16 with zeros
        padded = key_bytes + b'\x00' * (16 - len(key_bytes))
        test_decryption(padded, "padded_to_16")

        # Try the key as-is if it's 14 bytes (maybe the AES impl handles it)
        # Also try: maybe the return value should be base64-decoded
        try:
            decoded = base64.b64decode(key_bytes)
            if len(decoded) in (16, 24, 32):
                test_decryption(decoded, "b64decoded")
        except:
            pass


def test_decryption(key, label):
    """Test AES-ECB decryption on PES payload."""
    import os
    from urllib.parse import unquote

    YK_HEADER_SIZE = 34
    VIDEO_PID = 0x0100

    if len(key) not in (16, 24, 32):
        return

    ykv = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
    # Read manifest and get first TS segment
    fs = ykv.stat().st_size
    with ykv.open("rb") as f:
        f.seek(-16, os.SEEK_END)
        tr = f.read(16).decode("utf-8", "replace")
    lt = tr.split("\x00", 1)[0].strip()
    ml = int(lt)
    with ykv.open("rb") as f:
        f.seek(-(16 + ml), os.SEEK_END)
        raw = f.read(ml)
    manifest = json.loads(unquote(raw.decode("utf-8")))

    ts_segs = [m for m in manifest if str(m.get("name", "")).lower().endswith(".ts")]
    ts_segs.sort(key=lambda s: int(s["name"].split(".")[0]))
    seg = ts_segs[0]
    offset = int(seg["offset"])
    size = int(seg["size"])
    with ykv.open("rb") as f:
        f.seek(offset + YK_HEADER_SIZE)
        data = f.read(size - YK_HEADER_SIZE)

    # Get first video PES payload
    n_packets = len(data) // 188
    pes_payload = None
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
            break

    if not pes_payload:
        print(f"  {label}: No PES payload found")
        return

    # Test on PES payload
    n = (len(pes_payload) // 16) * 16
    if n > 0:
        try:
            dec = AES.new(key, AES.MODE_ECB).decrypt(pes_payload[:n])
            nal4 = dec.count(b"\x00\x00\x00\x01")
            nal3 = dec.count(b"\x00\x00\x01")
            if nal4 > 0 or nal3 > 0:
                print(f"  *** {label} ECB: nal4={nal4} nal3={nal3} first16={dec[:16].hex()}")
        except Exception as e:
            pass

    # Test on full TS data (first 1024 bytes)
    n2 = (1024 // 16) * 16
    try:
        dec2 = AES.new(key, AES.MODE_ECB).decrypt(data[:n2])
        nal4 = dec2.count(b"\x00\x00\x00\x01")
        nal3 = dec2.count(b"\x00\x00\x01")
        if nal4 > 0 or nal3 > 0:
            print(f"  *** {label} ECB(TS): nal4={nal4} nal3={nal3} first16={dec2[:16].hex()}")
    except:
        pass


if __name__ == "__main__":
    main()
