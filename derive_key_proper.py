"""Properly derive DRM key by implementing escape/decodeURIComponent in MiniRacer."""
import json
import base64
from pathlib import Path
from py_mini_racer import MiniRacer

R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc="

JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")


def main():
    js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")
    ctx = MiniRacer()

    # Set up browser environment WITH proper escape/decodeURIComponent
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

    // Proper implementation of escape() and decodeURIComponent()
    // escape() converts a string to %XX-encoded form for bytes > 127
    var escape = function(str) {
        var result = '';
        for (var i = 0; i < str.length; i++) {
            var c = str.charCodeAt(i);
            if (c > 127) {
                result += '%' + c.toString(16).toUpperCase().padStart(2, '0');
            } else if (c < 32 || c == 37 || c == 43 || c == 61 || c == 91 || c == 93 || c == 123 || c == 125 || c == 124 || c == 92 || c == 94 || c == 126 || c == 96 || c == 39 || c == 34) {
                result += '%' + c.toString(16).toUpperCase().padStart(2, '0');
            } else {
                result += str.charAt(i);
            }
        }
        return result;
    };

    // decodeURIComponent() decodes %XX sequences as UTF-8
    var decodeURIComponent = function(str) {
        // First, decode %XX to bytes
        var bytes = [];
        var i = 0;
        while (i < str.length) {
            if (str[i] == '%' && i + 2 < str.length) {
                var hex = str.substr(i+1, 2);
                bytes.push(parseInt(hex, 16));
                i += 3;
            } else {
                bytes.push(str.charCodeAt(i));
                i++;
            }
        }
        // Then, decode bytes as UTF-8
        var result = '';
        var j = 0;
        while (j < bytes.length) {
            var b = bytes[j];
            if (b < 128) {
                result += String.fromCharCode(b);
                j++;
            } else if (b >= 192 && b < 224 && j + 1 < bytes.length) {
                result += String.fromCharCode(((b & 31) << 6) | (bytes[j+1] & 63));
                j += 2;
            } else if (b >= 224 && b < 240 && j + 2 < bytes.length) {
                result += String.fromCharCode(((b & 15) << 12) | ((bytes[j+1] & 63) << 6) | (bytes[j+2] & 63));
                j += 3;
            } else if (b >= 240 && j + 3 < bytes.length) {
                var cp = ((b & 7) << 18) | ((bytes[j+1] & 63) << 12) | ((bytes[j+2] & 63) << 6) | (bytes[j+3] & 63);
                cp -= 0x10000;
                result += String.fromCharCode(0xD800 + (cp >> 10)) + String.fromCharCode(0xDC00 + (cp & 0x3FF));
                j += 4;
            } else {
                result += String.fromCharCode(b);
                j++;
            }
        }
        return result;
    };

    var encodeURIComponent = function(str) { return str; };
    var atob = function(s) {
        var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
        var str = s.replace(/=+$/, '');
        var result = '';
        for (var i = 0; i < str.length; i += 4) {
            var n = (chars.indexOf(str[i]) << 18) | (chars.indexOf(str[i+1]) << 12) |
                    (i+2 < str.length ? chars.indexOf(str[i+2]) << 6 : 0) |
                    (i+3 < str.length ? chars.indexOf(str[i+3]) : 0);
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
    print("Browser environment set up (with proper escape/decodeURIComponent)")

    # Load original JS WITHOUT patching
    try:
        ctx.eval(js_code)
        print("Original JS loaded successfully!")
    except Exception as e:
        print(f"JS execution failed: {e}")
        # Try to find and patch just the problematic part
        err_str = str(e)
        print(f"Error: {err_str[:500]}")

        # If the error is "d42hksldla", it's from the UTF-8 conversion
        if "d42hksldla" in err_str:
            print("\nUTF-8 conversion error detected. Trying alternative approach...")

            # Instead of patching the JS, let's intercept the function
            # Try calling _sce_dlgtqred with proper error handling
            code = """
            (function() {
                try {
                    var key = _sce_dlgtqred('""" + R1_RANDOM + """', '""" + ENCRYPTR_SERVER + """', '""" + COPYRIGHT_KEY + """');
                    return JSON.stringify({
                        type: typeof key,
                        length: key.length,
                        hex: Array.from(key).map(function(c) {
                            return (typeof c === 'number' ? c : c.charCodeAt(0)).toString(16).padStart(2, '0');
                        }).join(''),
                        constructor: key.constructor.name
                    });
                } catch(e) {
                    return JSON.stringify({error: e.message, stack: e.stack});
                }
            })();
            """
            try:
                result = ctx.eval(code)
                info = json.loads(result)
                print(f"\nResult: {json.dumps(info, indent=2)}")
            except Exception as e2:
                print(f"Alternative approach also failed: {e2}")
        return

    # If JS loaded successfully, call _sce_dlgtqred
    code = """
    (function() {
        try {
            var key = _sce_dlgtqred('""" + R1_RANDOM + """', '""" + ENCRYPTR_SERVER + """', '""" + COPYRIGHT_KEY + """');
            var info = { type: typeof key, hex: '', length: 0, constructor: '' };
            if (typeof key === 'string') {
                info.length = key.length;
                info.constructor = 'string';
                for (var i = 0; i < key.length; i++) {
                    info.hex += key.charCodeAt(i).toString(16).padStart(2, '0');
                }
            } else if (Array.isArray(key) || (key && key.length !== undefined)) {
                info.length = key.length;
                info.constructor = key.constructor ? key.constructor.name : 'array';
                for (var i = 0; i < key.length; i++) {
                    var v = typeof key[i] === 'number' ? key[i] : key[i].charCodeAt(0);
                    info.hex += (v & 0xFF).toString(16).padStart(2, '0');
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
    print(f"  type: {info.get('type')}")
    print(f"  length: {info.get('length')}")
    print(f"  hex: {info.get('hex')}")
    print(f"  constructor: {info.get('constructor')}")
    if info.get('error'):
        print(f"  error: {info['error']}")

    # Also try _sce_lgtcaygl and _sce_r_skjhfnck
    for func_name in ['_sce_lgtcaygl', '_sce_r_skjhfnck']:
        code2 = """
        (function() {
            try {
                var result = """ + func_name + ("""('""" + R1_RANDOM + """')""" if func_name == '_sce_lgtcaygl' else """()""") + """;
                var info = { type: typeof result, hex: '', length: 0, stringValue: '' };
                if (typeof result === 'string') {
                    info.length = result.length;
                    info.stringValue = result;
                    for (var i = 0; i < result.length; i++) {
                        info.hex += result.charCodeAt(i).toString(16).padStart(2, '0');
                    }
                } else if (result && result.length !== undefined) {
                    info.length = result.length;
                    for (var i = 0; i < result.length; i++) {
                        var v = typeof result[i] === 'number' ? result[i] : result[i].charCodeAt(0);
                        info.hex += (v & 0xFF).toString(16).padStart(2, '0');
                    }
                }
                return JSON.stringify(info);
            } catch(e) {
                return JSON.stringify({error: e.message});
            }
        })();
        """
        try:
            result2 = ctx.eval(code2)
            info2 = json.loads(result2)
            print(f"\n{func_name} result:")
            print(f"  type: {info2.get('type')}")
            print(f"  length: {info2.get('length')}")
            print(f"  hex: {info2.get('hex')}")
            if info2.get('stringValue'):
                print(f"  string: {info2['stringValue']}")
            if info2.get('error'):
                print(f"  error: {info2['error']}")
        except Exception as e:
            print(f"\n{func_name} failed: {e}")


if __name__ == "__main__":
    main()
