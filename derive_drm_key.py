"""Run Youku's obfuscated DRM JS to derive the decryption key using py_mini_racer (V8)."""
import json
import base64
import sys
from pathlib import Path
from py_mini_racer import MiniRacer

# DRM parameters from the YKV manifest for episode 1
R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc="

# JS files to try
JS_FILES = [
    Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js"),
    Path(r"D:\软件下载\YOUKU\9.5.2.1001\resources\assets\local_caches\static\9bfde36f7528f854b52055218f494ec0.js"),
]


def try_run_js(js_path: Path):
    """Try to load and execute the JS file, then call _sce_dlgtqred."""
    print(f"\n{'='*60}")
    print(f"Trying JS file: {js_path.name}")
    print(f"  Size: {js_path.stat().st_size} bytes")
    print(f"{'='*60}")

    js_code = js_path.read_text(encoding="utf-8", errors="replace")

    # Set up a minimal browser environment
    ctx = MiniRacer()

    # Inject browser globals
    setup_js = """
    var window = this;
    var self = this;
    var navigator = { userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' };
    var document = {
        createElement: function() { return { setAttribute: function(){}, appendChild: function(){}, style: {}, getContext: function(){ return null; } }; },
        getElementsByTagName: function() { return [{ appendChild: function(){} }]; },
        body: { appendChild: function(){} },
        head: { appendChild: function(){} },
        addEventListener: function(){},
        removeEventListener: function(){}
    };
    var location = { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:' };
    var atob = function(s) { return s; };  // simplified
    var btoa = function(s) { return s; };  // simplified
    var console = { log: function(){}, error: function(){}, warn: function(){} };
    """

    try:
        ctx.eval(setup_js)
        print("  [OK] Browser environment set up")
    except Exception as e:
        print(f"  [FAIL] Setup failed: {e}")
        return

    # Try to load the JS file
    try:
        ctx.eval(js_code)
        print("  [OK] JS file loaded and executed")
    except Exception as e:
        print(f"  [FAIL] JS execution failed: {e}")
        # Try wrapping in IIFE context
        try:
            ctx.eval(f"(function() {{ {js_code} }})();")
            print("  [OK] JS file loaded (wrapped in IIFE)")
        except Exception as e2:
            print(f"  [FAIL] Wrapped execution also failed: {e2}")
            return

    # Check which functions are available
    check_code = """
    var results = {};
    results._sce_dlgtqred = typeof _sce_dlgtqred;
    results._sce_lgtcaygl = typeof _sce_lgtcaygl;
    results._sce_r_skjhfnck = typeof _sce_r_skjhfnck;
    // Also check on window
    results.window_sce_dlgtqred = typeof window._sce_dlgtqred;
    results.window_sce_lgtcaygl = typeof window._sce_lgtcaygl;
    results.window_sce_r_skjhfnck = typeof window._sce_r_skjhfnck;
    // List all _sce_ properties
    results.all_sce = [];
    for (var k in window) {
        if (k.indexOf('_sce_') === 0) {
            results.all_sce.push(k + ':' + typeof window[k]);
        }
    }
    JSON.stringify(results);
    """
    try:
        result = ctx.eval(check_code)
        print(f"\n  Function availability:")
        result_dict = json.loads(result)
        for k, v in result_dict.items():
            if k == "all_sce":
                print(f"    all_sce: {v}")
            else:
                print(f"    {k}: {v}")
    except Exception as e:
        print(f"  [FAIL] Cannot check functions: {e}")

    # Try calling _sce_dlgtqred
    call_code = f"""
    (function() {{
        var R1 = '{R1_RANDOM}';
        var encryptRServer = '{ENCRYPTR_SERVER}';
        var copyrightKey = '{COPYRIGHT_KEY}';

        var key = null;
        var errors = [];

        // Try calling _sce_dlgtqred
        try {{
            if (typeof _sce_dlgtqred === 'function') {{
                key = _sce_dlgtqred(R1, encryptRServer, copyrightKey);
            }} else if (typeof window._sce_dlgtqred === 'function') {{
                key = window._sce_dlgtqred(R1, encryptRServer, copyrightKey);
            }}
        }} catch(e) {{
            errors.push('_sce_dlgtqred: ' + e.message);
        }}

        // Try calling _sce_lgtcaygl
        if (!key) {{
            try {{
                if (typeof _sce_lgtcaygl === 'function') {{
                    key = _sce_lgtcaygl(R1, encryptRServer, copyrightKey);
                }} else if (typeof window._sce_lgtcaygl === 'function') {{
                    key = window._sce_lgtcaygl(R1, encryptRServer, copyrightKey);
                }}
            }} catch(e) {{
                errors.push('_sce_lgtcaygl: ' + e.message);
            }}
        }}

        // Try calling _sce_r_skjhfnck
        if (!key) {{
            try {{
                if (typeof _sce_r_skjhfnck === 'function') {{
                    key = _sce_r_skjhfnck(R1, encryptRServer, copyrightKey);
                }} else if (typeof window._sce_r_skjhfnck === 'function') {{
                    key = window._sce_r_skjhfnck(R1, encryptRServer, copyrightKey);
                }}
            }} catch(e) {{
                errors.push('_sce_r_skjhfnck: ' + e.message);
            }}
        }}

        var result = {{ key: key, keyType: typeof key, errors: errors }};
        if (key) {{
            if (typeof key === 'string') {{
                result.keyLength = key.length;
                result.keyHex = '';
                for (var i = 0; i < key.length; i++) {{
                    var c = key.charCodeAt(i);
                    result.keyHex += c.toString(16).padStart(2, '0');
                }}
            }}
        }}
        return JSON.stringify(result);
    }})();
    """

    try:
        result = ctx.eval(call_code)
        print(f"\n  DRM key derivation result:")
        result_dict = json.loads(result)
        print(f"    key: {result_dict.get('key')}")
        print(f"    keyType: {result_dict.get('keyType')}")
        if result_dict.get('keyLength'):
            print(f"    keyLength: {result_dict['keyLength']}")
        if result_dict.get('keyHex'):
            print(f"    keyHex: {result_dict['keyHex']}")
        if result_dict.get('errors'):
            print(f"    errors: {result_dict['errors']}")
        return result_dict
    except Exception as e:
        print(f"  [FAIL] Key derivation call failed: {e}")
        return None


def main():
    for js_path in JS_FILES:
        if js_path.exists():
            result = try_run_js(js_path)
            if result and result.get("key"):
                print(f"\n\n*** SUCCESS! Key derived: {result['key']} ***")
                return
        else:
            print(f"  File not found: {js_path}")

    # If neither file worked, try to search for _sce_ in all JS files
    print(f"\n{'='*60}")
    print("Searching all JS files for _sce_ functions...")
    print(f"{'='*60}")
    static_dir = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static")
    if not static_dir.exists():
        static_dir = Path(r"D:\软件下载\YOUKU\9.5.2.1001\resources\assets\local_caches\static")

    if static_dir.exists():
        for js_file in sorted(static_dir.glob("*.js")):
            try:
                content = js_file.read_text(encoding="utf-8", errors="replace")
                if "_sce_" in content:
                    print(f"  Found _sce_ in: {js_file.name}")
            except:
                pass


if __name__ == "__main__":
    main()
