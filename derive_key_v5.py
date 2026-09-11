"""Hook CryptoJS AES operations to capture the actual decryption key."""
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

    // Patch decodeURIComponent to handle binary data
    var _orig_decodeURIComponent = decodeURIComponent;
    decodeURIComponent = function(s) {
        try { return _orig_decodeURIComponent(s); }
        catch(e) { return s.replace(/%([0-9A-Fa-f]{2})/g, function(_, hex) { return String.fromCharCode(parseInt(hex, 16)); }); }
    };

    // Storage for captured keys
    window.__captured_keys = [];
    window.__captured_aes_ops = [];

    // Helper: convert WordArray to hex string
    window.__wordArrayToHex = function(wa) {
        if (!wa || typeof wa !== 'object') return null;
        var words = wa.dw || wa.words;
        var sigBytes = wa.sioj || wa.sigBytes;
        if (!words || !sigBytes) return null;
        var hex = '';
        for (var i = 0; i < sigBytes; i++) {
            var b = (words[i >>> 2] >>> (24 - (i % 4) * 8)) & 0xff;
            hex += b.toString(16).padStart(2, '0');
        }
        return hex;
    };
    """
    ctx.eval(setup_js)

    # Load the JS code
    ctx.eval(js_code)

    # Now try to find and hook the CryptoJS AES module
    # The obfuscated code uses different names, but we can search for patterns
    hook_code = r"""
    (function() {
        var results = {};

        // Try to find AES-related objects by looking at all global variables
        // The AES key expansion uses the S-box [0,1,2,4,8,16,32,64,128,27,54]
        // We know _K (sesca) is the AES key expansion class

        // Search for objects with encrypt/decrypt methods
        var found = [];
        for (var k in window) {
            try {
                var v = window[k];
                if (typeof v === 'object' && v !== null) {
                    if (typeof v.encrypt === 'function' || typeof v.decrypt === 'function') {
                        found.push(k);
                    }
                    // Also check for _doFinalize pattern
                    for (var k2 in v) {
                        if (typeof v[k2] === 'function' && k2.indexOf('_fjui') >= 0) {
                            found.push(k + '.' + k2);
                        }
                    }
                }
            } catch(e) {}
        }
        results.aesObjects = found;

        // Try to call _sce_dlgtqred and capture intermediate results
        // by hooking the eval function used by the VM
        var orig_eval = eval;
        var eval_calls = [];
        // We can't easily hook eval in the VM, so let's try another approach

        // Let's try to call _sce_dlgtqred and get the result as hex
        try {
            var key = _sce_dlgtqred(
                'EmlTWqfjgNExE6ongWjf6w==',
                'rIsBBcYjaN88Fnj00PlLGQ==',
                '0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7j7M+vQc='
            );

            // The key might be a string with charCodes as bytes
            if (typeof key === 'string') {
                results.keyType = 'string';
                results.keyLength = key.length;
                results.keyHex = '';
                for (var i = 0; i < key.length; i++) {
                    results.keyHex += key.charCodeAt(i).toString(16).padStart(2, '0');
                }
                results.keyBase64 = btoa ? btoa(key) : null;
            } else if (Array.isArray(key)) {
                results.keyType = 'array';
                results.keyLength = key.length;
                results.keyHex = '';
                for (var i = 0; i < key.length; i++) {
                    results.keyHex += (key[i] & 0xFF).toString(16).padStart(2, '0');
                }
            } else if (typeof key === 'object' && key !== null) {
                results.keyType = 'object';
                results.keyKeys = Object.keys(key);
                // Check if it's a WordArray
                var hex = window.__wordArrayToHex(key);
                if (hex) {
                    results.keyHex = hex;
                }
                // Try toString
                try { results.keyToString = key.toString(); } catch(e) { results.keyToString = 'err: ' + e.message; }
            } else {
                results.keyType = typeof key;
                results.keyValue = key;
            }
        } catch(e) {
            results.error = e.message;
            results.stack = e.stack ? e.stack.substring(0, 1000) : null;
        }

        // Also try calling _sce_lgtcaygl and see if the result works differently
        try {
            var key2 = _sce_lgtcaygl(
                'EmlTWqfjgNExE6ongWjf6w==',
                'rIsBBcYjaN88Fnj00PlLGQ==',
                '0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7j7M+vQc='
            );
            results.key2Type = typeof key2;
            if (typeof key2 === 'string') {
                results.key2Value = key2;
                results.key2Length = key2.length;
                results.key2Hex = '';
                for (var i = 0; i < key2.length; i++) {
                    results.key2Hex += key2.charCodeAt(i).toString(16).padStart(2, '0');
                }
            }
        } catch(e) {
            results.key2Error = e.message;
        }

        // Try calling all three functions in sequence
        try {
            var r1 = _sce_r_skjhfnck(
                'EmlTWqfjgNExE6ongWjf6w==',
                'rIsBBcYjaN88Fnj00PlLGQ==',
                '0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7j7M+vQc='
            );
            results.r_skjhfnck_type = typeof r1;
            results.r_skjhfnck_value = r1;
        } catch(e) {
            results.r_skjhfnck_error = e.message;
        }

        return JSON.stringify(results);
    })();
    """

    result = ctx.eval(hook_code)
    info = json.loads(result)

    print("=== Results ===")
    for k, v in info.items():
        if isinstance(v, str) and len(v) > 200:
            print(f"  {k}: {v[:200]}...")
        else:
            print(f"  {k}: {v}")

    # If we got key hex, try it for decryption
    if info.get('keyHex'):
        key_hex = info['keyHex']
        key_bytes = bytes.fromhex(key_hex)
        print(f"\n=== Key as hex: {key_hex} ({len(key_bytes)}B) ===")
        # Try first 16, 24, etc.
        if len(key_bytes) >= 16:
            print(f"  First 16 bytes: {key_bytes[:16].hex()}")
        if len(key_bytes) >= 24:
            print(f"  First 24 bytes: {key_bytes[:24].hex()}")


if __name__ == "__main__":
    main()
