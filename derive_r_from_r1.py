"""Extract R1Random and derive the correct r value via _sce_r_skjhfnck."""
import os, json, base64
from pathlib import Path
from urllib.parse import unquote
from py_mini_racer import MiniRacer
from Crypto.Cipher import AES

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")

# read manifest
fs = YKV.stat().st_size
with YKV.open("rb") as f:
    f.seek(-16, os.SEEK_END)
    tr = f.read(16).decode("utf-8", "replace")
ml = int(tr.split("\x00",1)[0].strip())
with YKV.open("rb") as f:
    f.seek(-(16+ml), os.SEEK_END)
    raw = f.read(ml)
manifest = json.loads(unquote(raw.decode("utf-8")))

# Find dbInfo
dbinfo_entry = next(m for m in manifest if m.get("name") == "dbInfo")
info = dbinfo_entry["info"]
ci = info["configInfo"]

# Get R1Random
r1_random = ci.get("R1Random")
print(f"R1Random: {r1_random}")
print(f"R1Random decoded: {base64.b64decode(r1_random).hex()} ({len(base64.b64decode(r1_random))} bytes)")

# Get DRM params
ups_data = ci["ups"]["data"]["data"]
streams = ups_data["stream"]
s0 = streams[0]
encrypt_r_server = s0["encryptR_server"]
copyright_key = s0["stream_ext"]["copyright_key"]
print(f"encryptR_server: {encrypt_r_server}")
print(f"copyright_key: {copyright_key}")
print(f"drm_type: {s0['drm_type']}")

# Now load the Youku JS and call _sce_r_skjhfnck
print("\n=== Loading Youku JS ===")
js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")
ctx = MiniRacer()

setup_js = r"""
var window = this; var self = this; var global = this;
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
var console = { log: function(){}, error: function(){}, warn: function(){}, debug: function(){}, info: function(){} };
var escape = function(str) {
    var r=''; for(var i=0;i<str.length;i++){var c=str.charCodeAt(i);
    if(c>127){r+='%'+c.toString(16).toUpperCase().padStart(2,'0');}
    else if(c<32||c==37||c==43||c==61||c==91||c==93||c==123||c==125||c==124||c==92||c==94||c==126||c==96||c==39||c==34){r+='%'+c.toString(16).toUpperCase().padStart(2,'0');}
    else{r+=str.charAt(i);}} return r;
};
var decodeURIComponent = function(str) {
    var bytes=[]; var i=0;
    while(i<str.length){if(str[i]=='%'&&i+2<str.length){bytes.push(parseInt(str.substr(i+1,2),16));i+=3;}
    else{bytes.push(str.charCodeAt(i));i++;}}
    var result=''; var j=0;
    while(j<bytes.length){var b=bytes[j];
    if(b<128){result+=String.fromCharCode(b);j++;}
    else if(b>=192&&b<224&&j+1<bytes.length){result+=String.fromCharCode(((b&31)<<6)|(bytes[j+1]&63));j+=2;}
    else if(b>=224&&b<240&&j+2<bytes.length){result+=String.fromCharCode(((b&15)<<12)|((bytes[j+1]&63)<<6)|(bytes[j+2]&63));j+=3;}
    else if(b>=240&&j+3<bytes.length){var cp=((b&7)<<18)|((bytes[j+1]&63)<<12)|((bytes[j+2]&63)<<6)|(bytes[j+3]&63);cp-=0x10000;result+=String.fromCharCode(0xD800+(cp>>10))+String.fromCharCode(0xDC00+(cp&0x3FF));j+=4;}
    else{result+=String.fromCharCode(b);j++;}} return result;
};
var encodeURIComponent = function(str) { return str; };
var atob = function(s) {
    var chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    var str=s.replace(/=+$/,''); var result='';
    for(var i=0;i<str.length;i+=4){
    var n=(chars.indexOf(str[i])<<18)|(chars.indexOf(str[i+1])<<12)|(i+2<str.length?chars.indexOf(str[i+2])<<6:0)|(i+3<str.length?chars.indexOf(str[i+3]):0);
    result+=String.fromCharCode((n>>16)&255);
    if(i+2<str.length&&str[i+2]!='=')result+=String.fromCharCode((n>>8)&255);
    if(i+3<str.length&&str[i+3]!='=')result+=String.fromCharCode(n&255);} return result;
};
var btoa = function(s) {
    var chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'; var result='';
    for(var i=0;i<s.length;i+=3){
    var n=(s.charCodeAt(i)<<16)|(i+1<s.length?s.charCodeAt(i+1)<<8:0)|(i+2<s.length?s.charCodeAt(i+2):0);
    result+=chars[(n>>18)&63]; result+=chars[(n>>12)&63];
    result+=i+1<s.length?chars[(n>>6)&63]:'='; result+=i+2<s.length?chars[n&63]:'=';} return result;
};
"""

ctx.eval(setup_js)
# Patch the UTF-8 conversion issue
patched_js = js_code.replace(
    'decodeURIComponent(escape(f.stringify(r)))',
    'f.stringify(r)'
)
ctx.eval(patched_js)
print("JS loaded")

# Call _sce_r_skjhfnck(R1Random) to get r
code = """
(function() {
    try {
        var results = {};
        // _sce_r_skjhfnck
        var r = _sce_r_skjhfnck('%s');
        results.r_skjhfnck = {
            type: typeof r,
            value: typeof r === 'string' ? r : JSON.stringify(Array.from(r)),
            hex: typeof r === 'string' ? Array.from(r).map(function(c){return c.charCodeAt(0).toString(16).padStart(2,'0');}).join('') : ''
        };
        return JSON.stringify(results);
    } catch(e) {
        return JSON.stringify({error: e.message, stack: e.stack ? e.stack.substring(0,500) : ''});
    }
})();
""" % r1_random

result = ctx.eval(code)
info = json.loads(result)
print(f"\n_sce_r_skjhfnck result:")
print(json.dumps(info, indent=2))

if "error" in info:
    print("Failed, trying direct approaches")
    exit(1)

r_val = info["r_skjhfnck"]["value"]
print(f"\nr value: {r_val}")

# Now use copyrightDRM algorithm with this r
def copyright_drm(r, encrypt_r_server, copyright_key):
    crypto_1 = AES.new(r.encode(), AES.MODE_ECB)
    key_2 = crypto_1.decrypt(base64.b64decode(encrypt_r_server))
    crypto_2 = AES.new(key_2, AES.MODE_ECB)
    decrypted = crypto_2.decrypt(base64.b64decode(copyright_key))
    return key_2, decrypted

key_2, raw = copyright_drm(r_val, encrypt_r_server, copyright_key)
print(f"\ncopyrightDRM with derived r='{r_val}':")
print(f"  key_2: {key_2.hex()} ({len(key_2)}B)")
print(f"  raw decrypted: {raw.hex()} ({len(raw)}B)")
print(f"  raw as ASCII: {raw}")

# Try base64 round-trip
try:
    key_decoded = base64.b64decode(raw)
    key_reencoded = base64.b64encode(key_decoded).decode()
    print(f"  b64 decoded: {key_decoded.hex()} ({len(key_decoded)}B)")
    print(f"  b64 re-encoded: {key_reencoded}")
except Exception as e:
    print(f"  b64 round-trip failed: {e}")

# Test the key on PES payload
print("\n=== Testing key on PES payload ===")
VIDEO_PID = 0x0100
YK_HEADER = 34
ts_segs = [m for m in manifest if str(m.get("name","")).lower().endswith(".ts")]
ts_segs.sort(key=lambda s: int(s["name"].split(".")[0]))
seg = ts_segs[0]
off = int(seg["offset"]); sz = int(seg["size"])
with YKV.open("rb") as f:
    f.seek(off + YK_HEADER)
    data = f.read(sz - YK_HEADER)

# Get first video PES payload
pes_payload = None
n_packets = len(data) // 188
for i in range(n_packets):
    pkt = data[i * 188: (i + 1) * 188]
    if pkt[0] != 0x47: continue
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
            pes_payload = pes[9 + hdr_data_len:]
        break

if pes_payload:
    print(f"PES payload: {len(pes_payload)}B, first16: {pes_payload[:16].hex()}")
    # Test all possible key variants
    for key, label in [(key_2, "key_2"), (raw[:16], "raw[:16]"), (raw[16:], "raw[16:]"), (raw, "raw32")]:
        if len(key) not in (16, 24, 32): continue
        n = (len(pes_payload) // 16) * 16
        if n == 0: continue
        dec = AES.new(key, AES.MODE_ECB).decrypt(pes_payload[:n])
        nal4 = dec.count(b"\x00\x00\x00\x01")
        nal3 = dec.count(b"\x00\x00\x01")
        print(f"  {label}: nal4={nal4} nal3={nal3} first16={dec[:16].hex()}")
        if nal4 > 0:
            print(f"    *** MATCH! Key works!")
            print(f"    Key hex: {key.hex()}")
