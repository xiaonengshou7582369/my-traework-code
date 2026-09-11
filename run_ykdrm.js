// run_ykdrm.js - Load ykdrm.js and try to derive the decryption key
const fs = require('fs');
const vm = require('vm');
const crypto = require('crypto');

// DRM params for episode 1
const R1 = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";

// Load ykdrm.js
const jsCode = fs.readFileSync("ykdrm.js", "utf-8");
console.log(`ykdrm.js loaded: ${jsCode.length} chars\n`);

// Create a minimal browser-like context
const context = {
    console: console,
    // Basic globals
    parseInt, parseFloat, isNaN, isFinite,
    Date, Math, JSON, Array, Object, String, Number, Boolean,
    RegExp, Error, TypeError, RangeError, SyntaxError, ReferenceError,
    Uint8Array, Uint16Array, Uint32Array, Int8Array, Int16Array, Int32Array,
    Float32Array, Float64Array, ArrayBuffer, DataView,
    TextEncoder, TextDecoder, Map, Set, WeakMap, WeakSet,
    Promise, Symbol, Proxy, Reflect,
    btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
    atob: (s) => Buffer.from(s, 'base64').toString('binary'),
    escape, unescape, decodeURIComponent, encodeURIComponent, encodeURI, decodeURI,
    // Browser objects (stubs)
    navigator: { userAgent: 'Mozilla/5.0', platform: 'Win32', language: 'zh-CN' },
    document: { createElement: () => ({}), getElementById: () => null, addEventListener(){} },
    location: { href: 'https://www.youku.com/' },
    setTimeout: (fn) => { try { fn(); } catch(e) {} return 0; },
    clearTimeout(){}, setInterval: () => 0, clearInterval(){},
};
context.window = context;
context.self = context;
context.global = context;
context.globalThis = context;

vm.createContext(context);

// Execute the ykdrm.js code
try {
    vm.runInContext(jsCode, context, { timeout: 10000 });
    console.log("ykdrm.js executed successfully\n");
} catch (e) {
    console.log("Execution error:", e.message);
}

// Check what globals were set
const knownKeys = new Set(Object.keys(context));
console.log("Globals after execution:");
for (const key of Object.keys(context)) {
    if (!["console","parseInt","parseFloat","isNaN","isFinite","Date","Math","JSON","Array","Object","String","Number","Boolean","RegExp","Error","TypeError","RangeError","SyntaxError","ReferenceError","Uint8Array","Uint16Array","Uint32Array","Int8Array","Int16Array","Int32Array","Float32Array","Float64Array","ArrayBuffer","DataView","TextEncoder","TextDecoder","Map","Set","WeakMap","WeakSet","Promise","Symbol","Proxy","Reflect","btoa","atob","escape","unescape","decodeURIComponent","encodeURIComponent","encodeURI","decodeURI","navigator","document","location","setTimeout","clearTimeout","setInterval","clearInterval","window","self","global","globalThis"].includes(key)) {
        const val = context[key];
        console.log(`  ${key}: ${typeof val} = ${typeof val === 'function' ? '[function]' : typeof val === 'string' ? val.substring(0, 100) : String(val).substring(0, 100)}`);
    }
}

// Try to find and call the key derivation function
// The function might be named something like getDrmKey, copyrightDRM, etc.
const funcNames = Object.keys(context).filter(k => 
    typeof context[k] === 'function' && 
    !["console","parseInt","parseFloat","isNaN","isFinite","Date","Math","JSON","Array","Object","String","Number","Boolean","RegExp","Error","TypeError","RangeError","SyntaxError","ReferenceError","Uint8Array","Uint16Array","Uint32Array","Int8Array","Int16Array","Int32Array","Float32Array","Float64Array","ArrayBuffer","DataView","TextEncoder","TextDecoder","Map","Set","WeakMap","WeakSet","Promise","Symbol","Proxy","Reflect","btoa","atob","escape","unescape","decodeURIComponent","encodeURIComponent","encodeURI","decodeURI","setTimeout","clearTimeout","setInterval","clearInterval"].includes(k)
);
console.log(`\nCustom functions found: ${funcNames.length}`);
for (const name of funcNames) {
    console.log(`  ${name}: ${context[name].toString().substring(0, 200)}`);
}

// Try calling each function with our DRM params
console.log("\n=== Trying to call functions with DRM params ===");
for (const name of funcNames) {
    const fn = context[name];
    // Try various argument combinations
    const argSets = [
        [R1, ENCRYPTR_SERVER, COPYRIGHT_KEY],
        [R1, ENCRYPTR_SERVER, COPYRIGHT_KEY, "ECB"],
        [ENCRYPTR_SERVER, COPYRIGHT_KEY, R1],
    ];
    for (let i = 0; i < argSets.length; i++) {
        try {
            const result = fn(...argSets[i]);
            if (result !== undefined && result !== null) {
                console.log(`  ${name}(${argSets[i].map(a => typeof a === 'string' ? '"'+a.substring(0,30)+'"' : a).join(', ')}):`);
                console.log(`    type: ${typeof result}`);
                if (typeof result === 'string') {
                    console.log(`    value: ${result.substring(0, 200)}`);
                    // Try as AES key
                    try {
                        const keyBuf = Buffer.from(result, 'base64');
                        console.log(`    base64-decoded: ${keyBuf.toString('hex')} (${keyBuf.length}B)`);
                    } catch(e) {}
                    try {
                        const keyBuf = Buffer.from(result, 'hex');
                        console.log(`    hex-decoded: ${keyBuf.toString('hex')} (${keyBuf.length}B)`);
                    } catch(e) {}
                } else if (typeof result === 'object') {
                    console.log(`    value: ${JSON.stringify(result).substring(0, 300)}`);
                } else {
                    console.log(`    value: ${String(result).substring(0, 200)}`);
                }
            }
        } catch (e) {
            // silently skip errors
        }
    }
}
