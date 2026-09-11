"""Verify DRM key derivation and test decryption on episode 1."""
import os
import json
import base64
from pathlib import Path
from urllib.parse import unquote
from py_mini_racer import MiniRacer
from Crypto.Cipher import AES

YKV_PATH = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
DATA_JSON = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\data.json")
JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")
YK_HEADER_SIZE = 34
VIDEO_PID = 0x0100
AUDIO_PID = 0x0101


def read_manifest(ykv_path):
    fs = ykv_path.stat().st_size
    with ykv_path.open("rb") as f:
        f.seek(-16, os.SEEK_END)
        tr = f.read(16).decode("utf-8", "replace")
    lt = tr.split("\x00", 1)[0].strip()
    ml = int(lt)
    with ykv_path.open("rb") as f:
        f.seek(-(16 + ml), os.SEEK_END)
        raw = f.read(ml)
    return json.loads(unquote(raw.decode("utf-8")))


def extract_drm_params(manifest):
    """Find DRM params in the manifest (m3u8 or dbInfo)."""
    params = {}
    for item in manifest:
        name = str(item.get("name", ""))
        if name == "youku.m3u8":
            # m3u8 content might be embedded
            pass
        if name == "dbInfo":
            # dbInfo often holds DRM metadata
            pass
    return params


def get_r1_from_data_json(data_json_path):
    """Extract R1Random from youku data.json."""
    if not data_json_path.exists():
        return None
    try:
        data = json.loads(data_json_path.read_text(encoding="utf-8", errors="replace"))
    except Exception as e:
        print(f"Error reading data.json: {e}")
        return None
    # Search recursively for R1Random / R1random
    found = []
    def walk(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in ("r1random", "r1random_encode", "r1") and isinstance(v, str):
                    found.append((path + "/" + k, v))
                walk(v, path + "/" + k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, path + f"[{i}]")
    walk(data)
    return found


def setup_js_env():
    """Build a JS environment stub to run Youku's obfuscated DRM JS."""
    return r"""
var window = this;
var self = this;
var global = this;
var navigator = { userAgent: 'Mozilla/5.0', platform: 'Win32', language: 'zh-CN', canPlayType: function(){return '';} };
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


def patch_js(js_code):
    """Patch the JS to bypass UTF-8 conversion issues."""
    old_pattern = 'decodeURIComponent(escape(f.stringify(r)))'
    new_pattern = 'f.stringify(r)'
    if old_pattern in js_code:
        return js_code.replace(old_pattern, new_pattern)
    return js_code


def derive_key_via_js(r1, enc_r_server, copyright_key):
    """Use py_mini_racer to run Youku's DRM JS and derive the key."""
    ctx = MiniRacer()
    ctx.eval(setup_js_env())

    js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")
    js_code = patch_js(js_code)
    ctx.eval(js_code)

    # Inspect _sce_dlgtqred return
    inspect_code = """
    (function() {
        try {
            var r = _sce_dlgtqred(%r1%, %ers%, %ck%);
            var info = {
                typeof: typeof r,
                length: r && r.length !== undefined ? r.length : -1,
                hex: '',
                str: '',
                isString: typeof r === 'string'
            };
            if (r) {
                if (typeof r === 'string') {
                    info.str = r;
                    for (var i = 0; i < r.length; i++) info.hex += (r.charCodeAt(i) & 0xFF).toString(16).padStart(2,'0');
                } else if (r.length !== undefined) {
                    for (var i = 0; i < r.length; i++) {
                        var v = r[i];
                        if (typeof v === 'number') info.hex += (v & 0xFF).toString(16).padStart(2,'0');
                        else if (typeof v === 'string') info.hex += (v.charCodeAt(0) & 0xFF).toString(16).padStart(2,'0');
                    }
                }
            }
            return JSON.stringify(info);
        } catch(e) {
            return JSON.stringify({error: e.message});
        }
    })();
    """.replace("%r1%", f"'{r1}'").replace("%ers%", f"'{enc_r_server}'").replace("%ck%", f"'{copyright_key}'")

    result = ctx.eval(inspect_code)
    return json.loads(result)


def get_first_video_pes_payload(data):
    """Extract the first video PES payload from TS data."""
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
                return pes[payload_offset:]
    return None


def test_key_on_payload(key_bytes, pes_payload, label):
    """Test AES-ECB decryption and look for NAL start codes."""
    if len(key_bytes) not in (16, 24, 32):
        print(f"  {label}: key length {len(key_bytes)} not valid for AES")
        return False
    n = (len(pes_payload) // 16) * 16
    if n == 0:
        print(f"  {label}: PES payload too small")
        return False
    try:
        dec = AES.new(key_bytes, AES.MODE_ECB).decrypt(pes_payload[:n])
        nal4 = dec.count(b"\x00\x00\x00\x01")
        nal3 = dec.count(b"\x00\x00\x01")
        # Check for SPS/PPS NAL types (HEVC: 0x40-0x42 for VPS, 0x42 for SPS, 0x44 for PPS)
        has_hevc_nal = False
        for idx in [i+4 for i in range(len(dec)-4) if dec[i:i+4] == b"\x00\x00\x00\x01"]:
            if idx < len(dec):
                nal_type = (dec[idx] & 0x7E) >> 1  # HEVC NAL type
                if 32 <= nal_type <= 35:  # VPS=32, SPS=33, PPS=34
                    has_hevc_nal = True
                    break
        if nal4 > 0 or nal3 > 0 or has_hevc_nal:
            print(f"  *** {label}: nal4={nal4} nal3={nal3} hevc_nal={has_hevc_nal} first16={dec[:16].hex()}")
            return True
    except Exception as e:
        print(f"  {label}: decrypt error: {e}")
    return False


def main():
    print("=== Step 1: Read manifest and DRM params ===")
    manifest = read_manifest(YKV_PATH)
    ts_segs = [m for m in manifest if str(m.get("name", "")).lower().endswith(".ts")]
    ts_segs.sort(key=lambda s: int(s["name"].split(".")[0]))
    print(f"Manifest items: {len(manifest)}, TS segments: {len(ts_segs)}")
    print(f"Manifest item names: {[m.get('name') for m in manifest[:10]]}")

    # Look for dbInfo and m3u8 in manifest - show full structure
    for item in manifest:
        name = str(item.get("name", ""))
        if name in ("dbInfo", "youku.m3u8") or "db" in name.lower() or "m3u8" in name.lower():
            print(f"\n{name}: {json.dumps(item, ensure_ascii=False)[:300]}")

    # Read youku.m3u8 to find DRM params
    m3u8_item = next((m for m in manifest if m.get("name") == "youku.m3u8"), None)
    if m3u8_item and m3u8_item.get("offset") is not None:
        offset = int(m3u8_item["offset"])
        size = int(m3u8_item["size"])
        with YKV_PATH.open("rb") as f:
            f.seek(offset)
            m3u8_raw = f.read(size)
        m3u8_text = m3u8_raw.decode("utf-8", errors="replace")
        print(f"\nyouku.m3u8 content (first 2000 chars):")
        print(m3u8_text[:2000])
        # Search for DRM params in m3u8
        for pat in ["R1Random", "encryptR", "copyright_key", "copyrightKey", "DRM", "key", "encrypt"]:
            idx = m3u8_text.find(pat)
            if idx >= 0:
                print(f"\n  Found '{pat}' at {idx}: ...{m3u8_text[max(0,idx-30):idx+150]}...")

    # Check dbInfo structure
    dbinfo_item = next((m for m in manifest if m.get("name") == "dbInfo"), None)
    if dbinfo_item:
        print(f"\ndbInfo full: {json.dumps(dbinfo_item, ensure_ascii=False)}")
        # dbInfo might have inline content instead of offset/size
        for k, v in dbinfo_item.items():
            if isinstance(v, str) and len(v) > 20:
                print(f"  dbInfo.{k}: {v[:200]}")

    print("\n=== Step 2: Get R1Random from data.json ===")
    r1_values = get_r1_from_data_json(DATA_JSON)
    if r1_values:
        print(f"Found {len(r1_values)} R1 values in data.json:")
        for p, v in r1_values[:10]:
            print(f"  {p}: {v}")
    else:
        print("No R1Random found in data.json, will use known value from episode 1")

    # Use the known DRM params from episode 1 (from previous analysis)
    R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
    ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
    COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc="
    print(f"\nUsing DRM params (from previous analysis):")
    print(f"  R1Random: {R1_RANDOM}")
    print(f"  encryptR_server: {ENCRYPTR_SERVER}")
    print(f"  copyright_key: {COPYRIGHT_KEY}")

    print("\n=== Step 3: Extract first TS segment and PES payload ===")
    seg = ts_segs[0]
    offset = int(seg["offset"])
    size = int(seg["size"])
    with YKV_PATH.open("rb") as f:
        f.seek(offset + YK_HEADER_SIZE)
        data = f.read(size - YK_HEADER_SIZE)
    print(f"Segment 1: {len(data)} bytes ({len(data)//188} TS packets)")

    pes_payload = get_first_video_pes_payload(data)
    if pes_payload:
        print(f"First video PES payload: {len(pes_payload)}B, first16: {pes_payload[:16].hex()}")
        # Check if already has NAL start codes (unencrypted)
        nal4 = pes_payload.count(b"\x00\x00\x00\x01")
        nal3 = pes_payload.count(b"\x00\x00\x01")
        print(f"  PES payload NAL check: nal4={nal4} nal3={nal3}")
    else:
        print("No video PES payload found!")
        return

    print("\n=== Step 4: Derive key via py_mini_racer (JS execution) ===")
    info = derive_key_via_js(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY)
    print(f"JS key info: {json.dumps(info, indent=2)}")

    print("\n=== Step 5: Test all key variants ===")
    tested = 0

    # Test the JS-derived key
    if info.get("hex"):
        key_bytes = bytes.fromhex(info["hex"])
        print(f"\nJS-derived key ({len(key_bytes)}B): {info['hex']}")
        # Try all 16-byte windows
        for i in range(len(key_bytes) - 15):
            k = key_bytes[i:i+16]
            if test_key_on_payload(k, pes_payload, f"js_key[{i}:{i+16}]"):
                tested += 1
        # Pad if shorter
        if 0 < len(key_bytes) < 16:
            padded = key_bytes + b'\x00' * (16 - len(key_bytes))
            if test_key_on_payload(padded, pes_payload, "js_key_padded"):
                tested += 1
        # Try as string -> base64 decode
        if info.get("str"):
            try:
                decoded = base64.b64decode(info["str"])
                if len(decoded) in (16, 24, 32):
                    if test_key_on_payload(decoded, pes_payload, "js_str_b64decoded"):
                        tested += 1
            except:
                pass

    # Test yk.py algorithm variants
    print("\n--- yk.py algorithm variants ---")
    r1_dec = base64.b64decode(R1_RANDOM)
    enc_server_dec = base64.b64decode(ENCRYPTR_SERVER)
    ckey_dec = base64.b64decode(COPYRIGHT_KEY)
    print(f"  r1_decoded: {len(r1_dec)}B = {r1_dec.hex()}")
    print(f"  enc_server_decoded: {len(enc_server_dec)}B = {enc_server_dec.hex()}")
    print(f"  copyright_key_decoded: {len(ckey_dec)}B = {ckey_dec.hex()}")

    # key_2 = AES_ECB_decrypt(enc_server, r1)
    key_2 = AES.new(r1_dec, AES.MODE_ECB).decrypt(enc_server_dec)
    print(f"  key_2 (AES_decrypt(encServer, r1)): {key_2.hex()}")
    if test_key_on_payload(key_2, pes_payload, "key_2"):
        tested += 1

    # raw = AES_ECB_decrypt(copyright_key, key_2)
    raw = AES.new(key_2, AES.MODE_ECB).decrypt(ckey_dec)
    print(f"  raw (AES_decrypt(ckey, key_2)): {raw.hex()}")
    if test_key_on_payload(raw[:16], pes_payload, "raw[:16]"):
        tested += 1
    if test_key_on_payload(raw[16:], pes_payload, "raw[16:]"):
        tested += 1

    # Direct keys
    if test_key_on_payload(r1_dec, pes_payload, "r1_decoded"):
        tested += 1
    if test_key_on_payload(enc_server_dec, pes_payload, "enc_server_decoded"):
        tested += 1
    if test_key_on_payload(ckey_dec[:16], pes_payload, "ckey[:16]"):
        tested += 1
    if test_key_on_payload(ckey_dec[16:], pes_payload, "ckey[16:]"):
        tested += 1

    # Fixed r values from yk.py
    R_FIXED_OLD = b"xWrtQpP4Z4RsrRCY"
    R_FIXED_B64 = base64.b64decode("aq1mVooivzaolmJY5NrQ3A==")
    if test_key_on_payload(R_FIXED_OLD, pes_payload, "R_FIXED_OLD"):
        tested += 1
    if test_key_on_payload(R_FIXED_B64, pes_payload, "R_FIXED_B64"):
        tested += 1

    # Combined: key_2 + raw[:16] or raw[16:]
    combined = key_2 + raw[:16]
    if len(combined) == 32:
        if test_key_on_payload(combined, pes_payload, "key_2+raw[:16]"):
            tested += 1

    print(f"\n=== Result: {tested} key(s) produced NAL start codes ===")


if __name__ == "__main__":
    main()
