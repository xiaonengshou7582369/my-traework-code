"""Fix the _sce_dlgtqred error by patching decodeURIComponent to handle binary data."""
import json
import base64
from pathlib import Path
from py_mini_racer import MiniRacer

R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w=="
ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ=="
COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc="

JS_FILE = Path(r"C:\Users\Administrator\AppData\Roaming\youku-app\local_caches\static\904ddb4d0e70418993e1854359d9b066.js")


def setup_and_run():
    ctx = MiniRacer()

    # Patch decodeURIComponent to handle binary data (never throw)
    setup_js = """
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

    // Patch decodeURIComponent to handle binary data
    var _orig_decodeURIComponent = decodeURIComponent;
    decodeURIComponent = function(s) {
        try {
            return _orig_decodeURIComponent(s);
        } catch(e) {
            // If it fails, manually decode %XX sequences
            return s.replace(/%([0-9A-Fa-f]{2})/g, function(_, hex) {
                return String.fromCharCode(parseInt(hex, 16));
            });
        }
    };

    // Also patch escape to handle all characters
    var _orig_escape = escape;
    escape = function(s) {
        return _orig_escape(s);
    };
    """
    ctx.eval(setup_js)

    js_code = JS_FILE.read_text(encoding="utf-8", errors="replace")
    ctx.eval(js_code)

    # Now try calling _sce_dlgtqred
    code = f"""
    (function() {{
        var R1 = '{R1_RANDOM}';
        var encryptRServer = '{ENCRYPTR_SERVER}';
        var copyrightKey = '{COPYRIGHT_KEY}';
        try {{
            var key = _sce_dlgtqred(R1, encryptRServer, copyrightKey);
            var result = {{
                success: true,
                value: key,
                type: typeof key,
                length: typeof key === 'string' ? key.length : null,
                hex: ''
            }};
            if (typeof key === 'string') {{
                for (var i = 0; i < key.length; i++) {{
                    result.hex += key.charCodeAt(i).toString(16).padStart(2, '0');
                }}
            }}
            return JSON.stringify(result);
        }} catch(e) {{
            return JSON.stringify({{
                success: false,
                error: e.message,
                stack: e.stack ? e.stack.substring(0, 1500) : null
            }});
        }}
    }})();
    """
    result = ctx.eval(code)
    result_dict = json.loads(result)

    if result_dict.get('success'):
        print(f"SUCCESS!")
        print(f"  Key value: {result_dict['value']}")
        print(f"  Type: {result_dict['type']}")
        print(f"  Length: {result_dict.get('length')}")
        print(f"  Hex: {result_dict.get('hex')}")
        return result_dict
    else:
        print(f"FAILED: {result_dict['error']}")
        if result_dict.get('stack'):
            print(f"Stack:\n{result_dict['stack']}")
        return result_dict


if __name__ == "__main__":
    result = setup_and_run()
