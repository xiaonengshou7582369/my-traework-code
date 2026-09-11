"""Deep investigation of _sce_dlgtqred's return value."""
import json
import base64
from pathlib import Path
from py_mini_racer import MiniRacer

R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc="

JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")


def main():
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

    var _orig_decodeURIComponent = decodeURIComponent;
    decodeURIComponent = function(s) {
        try { return _orig_decodeURIComponent(s); }
        catch(e) { return s.replace(/%([0-9A-Fa-f]{2})/g, function(_, hex) { return String.fromCharCode(parseInt(hex, 16)); }); }
    };
    """
    ctx.eval(setup_js)
    js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")
    ctx.eval(js_code)

    # Call _sce_dlgtqred and examine the result
    code = "(function() {" \
        "var R1 = '" + R1_RANDOM + "';" \
        "var encryptRServer = '" + ENCRYPTR_SERVER + "';" \
        "var copyrightKey = '" + COPYRIGHT_KEY + "';" \
        "var key = _sce_dlgtqred(R1, encryptRServer, copyrightKey);" \
        "var info = {" \
        "  type: typeof key," \
        "  isArray: Array.isArray(key)," \
        "  keys: []," \
        "  properties: {}," \
        "  constructorName: ''," \
        "  toString: ''," \
        "  valueOf: ''" \
        "};" \
        "try { info.constructorName = key.constructor ? key.constructor.name : 'unknown'; } catch(e) {}" \
        "try { info.toString = key.toString(); } catch(e) { info.toString = 'err: ' + e.message; }" \
        "try { info.valueOf = String(key.valueOf()); } catch(e) { info.valueOf = 'err: ' + e.message; }" \
        "if (typeof key === 'object' && key !== null) {" \
        "  for (var k in key) {" \
        "    if (key.hasOwnProperty(k)) {" \
        "      var val = key[k];" \
        "      info.keys.push(k);" \
        "      if (Array.isArray(val)) {" \
        "        info.properties[k] = { type: 'array', length: val.length, values: val.slice(0, 50) };" \
        "      } else if (typeof val === 'object' && val !== null) {" \
        "        info.properties[k] = { type: 'object', keys: Object.keys(val).slice(0, 20) };" \
        "      } else {" \
        "        info.properties[k] = { type: typeof val, value: val };" \
        "      }" \
        "    }" \
        "  }" \
        "}" \
        "if (Array.isArray(key)) {" \
        "  info.arrayValues = key;" \
        "  info.arrayLength = key.length;" \
        "  info.arrayHex = '';" \
        "  for (var i = 0; i < key.length; i++) {" \
        "    info.arrayHex += (key[i] & 0xFF).toString(16).padStart(2, '0');" \
        "  }" \
        "}" \
        "return JSON.stringify(info);" \
        "})();"

    result = ctx.eval(code)
    info = json.loads(result)

    print(f"Type: {info['type']}")
    print(f"IsArray: {info['isArray']}")
    print(f"Constructor: {info['constructorName']}")
    print(f"ToString: '{info['toString']}'")
    print(f"ValueOf: '{info.get('valueOf')}'")
    print(f"Keys: {info.get('keys')}")

    if info.get('arrayValues'):
        print(f"\nArray values: {info['arrayValues']}")
        print(f"Array length: {info['arrayLength']}")
        print(f"Array hex: {info['arrayHex']}")

    if info.get('properties'):
        print(f"\nProperties:")
        for k, v in info['properties'].items():
            print(f"  {k}: {v}")

    # Try the toString value as the key
    ts = info.get('toString', '')
    if ts and ts != 'err':
        print(f"\n=== Trying toString as key: '{ts}' ===")
        # Try as base64 string
        try:
            decoded = base64.b64decode(ts)
            print(f"  base64-decoded: {decoded.hex()} ({len(decoded)}B)")
        except:
            print(f"  Not valid base64")
        # Try as raw bytes
        raw = ts.encode()
        print(f"  ASCII bytes: {raw.hex()} ({len(raw)}B)")

    # Also check what _sce_lgtcaygl returns (it returned a string before)
    code2 = "(function() {" \
        "var R1 = '" + R1_RANDOM + "';" \
        "var encryptRServer = '" + ENCRYPTR_SERVER + "';" \
        "var copyrightKey = '" + COPYRIGHT_KEY + "';" \
        "var key = _sce_lgtcaygl(R1, encryptRServer, copyrightKey);" \
        "var info = { type: typeof key, value: key, toString: '' };" \
        "try { info.toString = key.toString(); } catch(e) { info.toString = 'err: ' + e.message; }" \
        "return JSON.stringify(info);" \
        "})();"
    result2 = ctx.eval(code2)
    info2 = json.loads(result2)
    print(f"\n=== _sce_lgtcaygl result ===")
    print(f"  type: {info2['type']}")
    print(f"  value: {info2.get('value')}")
    print(f"  toString: '{info2.get('toString')}'")


if __name__ == "__main__":
    main()
