"""Try each _sce_ function separately and investigate the error."""
import json
import base64
from pathlib import Path
from py_mini_racer import MiniRacer

R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc="

JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")


def setup_context():
    """Set up a V8 context with browser environment."""
    ctx = MiniRacer()

    setup_js = """
    var window = this;
    var self = this;
    var global = this;
    var navigator = {
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        platform: 'Win32',
        language: 'zh-CN',
        appVersion: '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    };
    var document = {
        createElement: function() { return { setAttribute: function(){}, appendChild: function(){}, style: {}, getContext: function(){ return null; }, addEventListener: function(){} }; },
        getElementsByTagName: function() { return [{ appendChild: function(){}, addEventListener: function(){} }]; },
        getElementById: function() { return null; },
        querySelector: function() { return null; },
        body: { appendChild: function(){}, addEventListener: function(){} },
        head: { appendChild: function(){} },
        addEventListener: function(){},
        removeEventListener: function(){},
        cookie: '',
        referrer: '',
        title: '',
        URL: 'https://www.youku.com/',
        domain: 'youku.com'
    };
    var location = { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:', pathname: '/', search: '', hash: '' };
    var localStorage = { getItem: function(){ return null; }, setItem: function(){}, removeItem: function(){} };
    var sessionStorage = { getItem: function(){ return null; }, setItem: function(){}, removeItem: function(){} };
    var performance = { now: function(){ return Date.now(); }, timing: { navigationStart: 0 } };
    var console = { log: function(){}, error: function(){}, warn: function(){}, debug: function(){}, info: function(){} };

    // Proper atob/btoa implementations
    var _b64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
    function atob(s) {
        s = s.replace(/=+$/, '');
        var bytes = [];
        for (var i = 0; i < s.length; i += 4) {
            var n = (_b64chars.indexOf(s[i]) << 18) | (_b64chars.indexOf(s[i+1]) << 12);
            if (i+2 < s.length) n |= (_b64chars.indexOf(s[i+2]) << 6);
            if (i+3 < s.length) n |= _b64chars.indexOf(s[i+3]);
            bytes.push((n >> 16) & 0xFF);
            if (i+2 < s.length) bytes.push((n >> 8) & 0xFF);
            if (i+3 < s.length) bytes.push(n & 0xFF);
        }
        return String.fromCharCode.apply(null, bytes);
    }
    function btoa(s) {
        var ret = '';
        for (var i = 0; i < s.length; i += 3) {
            var n = (s.charCodeAt(i) << 16) | ((i+1 < s.length ? s.charCodeAt(i+1) : 0) << 8) | (i+2 < s.length ? s.charCodeAt(i+2) : 0);
            ret += _b64chars[(n >> 18) & 0x3F];
            ret += _b64chars[(n >> 12) & 0x3F];
            ret += i+1 < s.length ? _b64chars[(n >> 6) & 0x3F] : '=';
            ret += i+2 < s.length ? _b64chars[n & 0x3F] : '=';
        }
        return ret;
    }

    // Crypto stub
    var CryptoJS = undefined;
    """
    ctx.eval(setup_js)

    js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")
    ctx.eval(js_code)

    return ctx


def try_function(ctx, func_name, *args):
    """Try calling a function with given args."""
    args_js = ", ".join(f"'{a}'" for a in args)
    code = f"""
    (function() {{
        var result = {{ success: false, value: null, error: null, type: null }};
        try {{
            var fn = typeof window.{func_name} === 'function' ? window.{func_name} : (typeof {func_name} === 'function' ? {func_name} : null);
            if (!fn) {{
                result.error = '{func_name} not found';
                return JSON.stringify(result);
            }}
            result.value = fn({args_js});
            result.success = true;
            result.type = typeof result.value;
            if (typeof result.value === 'string') {{
                result.length = result.value.length;
                result.hex = '';
                for (var i = 0; i < result.value.length; i++) {{
                    result.hex += result.value.charCodeAt(i).toString(16).padStart(2, '0');
                }}
            }}
        }} catch(e) {{
            result.error = e.message;
            result.stack = e.stack ? e.stack.substring(0, 500) : null;
        }}
        return JSON.stringify(result);
    }})();
    """
    result = ctx.eval(code)
    return json.loads(result)


def main():
    ctx = setup_context()
    print("JS loaded. Testing each _sce_ function:\n")

    # Test each function individually with all 3 parameters
    for func in ["_sce_dlgtqred", "_sce_lgtcaygl", "_sce_r_skjhfnck"]:
        print(f"{'='*50}")
        print(f"Testing: {func}(R1, encryptR_server, copyright_key)")
        print(f"{'='*50}")
        result = try_function(ctx, func, R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY)
        print(f"  success: {result.get('success')}")
        print(f"  value: {result.get('value')}")
        print(f"  type: {result.get('type')}")
        if result.get('length'):
            print(f"  length: {result['length']}")
        if result.get('hex'):
            print(f"  hex: {result['hex']}")
        if result.get('error'):
            print(f"  error: {result['error']}")
        if result.get('stack'):
            print(f"  stack: {result['stack']}")
        print()

    # Try different parameter orders
    print(f"{'='*50}")
    print("Trying different parameter orders for _sce_dlgtqred:")
    print(f"{'='*50}")

    combos = [
        ("encryptR_server, copyright_key, R1", ENCRYPTR_SERVER, COPYRIGHT_KEY, R1_RANDOM),
        ("copyright_key, R1, encryptR_server", COPYRIGHT_KEY, R1_RANDOM, ENCRYPTR_SERVER),
        ("R1 only", R1_RANDOM),
        ("encryptR_server only", ENCRYPTR_SERVER),
        ("copyright_key only", COPYRIGHT_KEY),
    ]
    for label, *args in combos:
        result = try_function(ctx, "_sce_dlgtqred", *args)
        if result.get('success') and result.get('value'):
            print(f"  {label}: value={result['value']}")
        elif result.get('error'):
            print(f"  {label}: error={result['error']}")
        else:
            print(f"  {label}: no result")

    # Try calling _sce_dlgtqred with 2 args (maybe R1 is derived internally)
    print(f"\n{'='*50}")
    print("Trying _sce_dlgtqred with 2 args:")
    print(f"{'='*50}")
    for label, *args in [
        ("encryptR_server, copyright_key", ENCRYPTR_SERVER, COPYRIGHT_KEY),
        ("R1, encryptR_server", R1_RANDOM, ENCRYPTR_SERVER),
        ("R1, copyright_key", R1_RANDOM, COPYRIGHT_KEY),
    ]:
        result = try_function(ctx, "_sce_dlgtqred", *args)
        if result.get('success') and result.get('value'):
            print(f"  {label}: value={result['value']}")
        elif result.get('error'):
            print(f"  {label}: error={result['error']}")
        else:
            print(f"  {label}: no result")

    # Try chaining functions
    print(f"\n{'='*50}")
    print("Trying function chains:")
    print(f"{'='*50}")

    # _sce_lgtcaygl -> _sce_dlgtqred
    r1 = try_function(ctx, "_sce_lgtcaygl", R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY)
    if r1.get('value'):
        r2 = try_function(ctx, "_sce_dlgtqred", r1['value'], ENCRYPTR_SERVER, COPYRIGHT_KEY)
        print(f"  lgtcaygl -> dlgtqred: {r2.get('value') or r2.get('error')}")

    # _sce_r_skjhfnck -> _sce_dlgtqred
    r1 = try_function(ctx, "_sce_r_skjhfnck", R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY)
    if r1.get('value'):
        r2 = try_function(ctx, "_sce_dlgtqred", r1['value'], ENCRYPTR_SERVER, COPYRIGHT_KEY)
        print(f"  r_skjhfnck -> dlgtqred: {r2.get('value') or r2.get('error')}")

    # Try calling _sce_dlgtqred with base64-decoded R1
    r1_decoded = base64.b64decode(R1_RANDOM)
    r1_hex = r1_decoded.hex()
    print(f"\n  Trying with R1 as hex string: {r1_hex}")
    result = try_function(ctx, "_sce_dlgtqred", r1_hex, ENCRYPTR_SERVER, COPYRIGHT_KEY)
    print(f"  result: {result.get('value') or result.get('error')}")


if __name__ == "__main__":
    main()
