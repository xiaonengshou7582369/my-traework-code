// debug_drm_node.js - Debug DRM JS execution in Node.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";

const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";

// Create a browser-like context with ALL needed globals
const context = {};

// Set up all standard JS globals
Object.assign(context, {
    navigator: {
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        platform: 'Win32',
        language: 'zh-CN',
        canPlayType: function() { return ''; },
        plugins: { length: 0 },
        mimeTypes: { length: 0 },
    },
    document: {
        createElement: function() {
            return { setAttribute: function() {}, appendChild: function() {}, style: {}, getContext: function() { return null; }, addEventListener: function() {}, removeEventListener: function() {}, innerHTML: '', src: '' };
        },
        getElementsByTagName: function() { return [{ appendChild: function() {}, addEventListener: function() {} }]; },
        getElementById: function() { return null; },
        body: { appendChild: function() {}, addEventListener: function() {} },
        head: { appendChild: function() {} },
        addEventListener: function() {}, removeEventListener: function() {},
        cookie: '', referrer: '', title: '', URL: 'https://www.youku.com/', domain: 'youku.com', documentElement: { style: {} },
    },
    location: { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:', pathname: '/', search: '', hash: '', origin: 'https://www.youku.com' },
    localStorage: { getItem: function() { return null; }, setItem: function() {}, removeItem: function() {}, clear: function() {}, key: function() { return null; }, length: 0 },
    sessionStorage: { getItem: function() { return null; }, setItem: function() {}, removeItem: function() {}, clear: function() {}, key: function() { return null; }, length: 0 },
    performance: { now: function() { return Date.now(); }, timing: { navigationStart: 0 }, getEntries: function() { return []; } },
    screen: { width: 1920, height: 1080 },
    history: { pushState: function() {}, replaceState: function() {}, back: function() {}, forward: function() {}, go: function() {} },
    btoa: function(s) { return Buffer.from(s, 'binary').toString('base64'); },
    atob: function(s) { return Buffer.from(s, 'base64').toString('binary'); },
    escape: escape, unescape: unescape,
    decodeURIComponent: decodeURIComponent, encodeURIComponent: encodeURIComponent,
    encodeURI: encodeURI, decodeURI: decodeURI,
    parseInt: parseInt, parseFloat: parseFloat, isNaN: isNaN, isFinite: isFinite,
    setTimeout: function(fn) { try { fn(); } catch(e) {} return 0; },
    clearTimeout: function() {}, setInterval: function() { return 0; }, clearInterval: function() {},
    Date: Date, Math: Math, JSON: JSON, Array: Array, Object: Object, String: String, Number: Number, Boolean: Boolean,
    RegExp: RegExp, Error: Error, TypeError: TypeError, RangeError: RangeError, SyntaxError: SyntaxError, ReferenceError: ReferenceError,
    Uint8Array: Uint8Array, Uint16Array: Uint16Array, Uint32Array: Uint32Array, Int8Array: Int8Array, Int16Array: Int16Array, Int32Array: Int32Array,
    Float32Array: Float32Array, Float64Array: Float64Array, ArrayBuffer: ArrayBuffer, DataView: DataView,
    TextEncoder: TextEncoder, TextDecoder: TextDecoder, Map: Map, Set: Set, WeakMap: WeakMap, WeakSet: WeakSet,
    Promise: Promise, Symbol: Symbol, Proxy: Proxy, Reflect: Reflect,
    console: { log: function() {}, error: function() {}, warn: function() {}, debug: function() {}, info: function() {}, trace: function() {} },
    Image: function() {}, XMLHttpRequest: function() { this.open = function() {}; this.send = function() {}; this.setRequestHeader = function() {}; this.addEventListener = function() {}; },
    fetch: function() { return Promise.resolve({ json: function() { return Promise.resolve({}); }, text: function() { return Promise.resolve(''); } }); },
    MessageChannel: function() { this.port1 = { postMessage: function() {} }; this.port2 = { onmessage: null }; },
    crypto: { getRandomValues: function(arr) { for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256); return arr; }, subtle: {} },
    URL: URL, URLSearchParams: URLSearchParams,
    Intl: Intl,
});

// Make window, self, global, globalThis all point to context
context.window = context;
context.self = context;
context.global = context;
context.globalThis = context;

// Create VM context
vm.createContext(context);

// Read and patch the DRM JS
const jsCode = fs.readFileSync(JS_FILE, 'utf-8');

// Patch 1: Fix the UTF-8 stringify
let patchedJs = jsCode.replace(
    'decodeURIComponent(escape(f.stringify(r)))',
    'f.stringify(r)'
);

// Execute the DRM JS
try {
    vm.runInContext(patchedJs, context, { filename: '904ddb4d.js', timeout: 30000 });
    console.log('DRM JS loaded successfully');
} catch (e) {
    console.log('DRM JS load error:', e.message);
    process.exit(1);
}

// Debug str16ToBytes
console.log('\n=== Debug str16ToBytes ===');
if (typeof context.str16ToBytes === 'function') {
    // Try to get the function source
    console.log('str16ToBytes source:', context.str16ToBytes.toString().substring(0, 500));

    // Try different inputs
    const testStrings = [
        "xWrtQpP4Z4RsrRCY",      // 16 chars
        "EmlTWqfjgNExE6ongWjf6w==", // R1Random
        "0123456789abcdef",       // 16 chars hex
        "aq1mVooivzaolmJY",       // 16 chars (from self.R without ==)
    ];

    for (const s of testStrings) {
        try {
            const result = context.str16ToBytes(s);
            console.log(`str16ToBytes("${s}") =`, JSON.stringify(result));
        } catch (e) {
            console.log(`str16ToBytes("${s}") error:`, e.message);
        }
    }
}

// Debug _sce_r_skjhfnck
console.log('\n=== Debug _sce_r_skjhfnck ===');
if (typeof context._sce_r_skjhfnck === 'function') {
    console.log('_sce_r_skjhfnck source:', context._sce_r_skjhfnck.toString().substring(0, 500));

    const testInputs = [
        "EmlTWqfjgNExE6ongWjf6w==",  // R1Random
        "xWrtQpP4Z4RsrRCY",          // Fixed r
        "0123456789abcdef",          // 16 chars
        "aq1mVooivzaolmJY5NrQ3A==", // self.R
    ];

    for (const s of testInputs) {
        try {
            const result = context._sce_r_skjhfnck(s);
            console.log(`_sce_r_skjhfnck("${s}") =`, JSON.stringify(result));
            if (typeof result === 'string') {
                console.log(`  hex: ${Buffer.from(result, 'binary').toString('hex')}`);
            }
        } catch (e) {
            console.log(`_sce_r_skjhfnck("${s}") error:`, e.message);
        }
    }
}

// Debug _sce_lgtcaygl
console.log('\n=== Debug _sce_lgtcaygl ===');
if (typeof context._sce_lgtcaygl === 'function') {
    console.log('_sce_lgtcaygl source:', context._sce_lgtcaygl.toString().substring(0, 500));

    const testInputs = [
        "EmlTWqfjgNExE6ongWjf6w==",
        "xWrtQpP4Z4RsrRCY",
    ];

    for (const s of testInputs) {
        try {
            const result = context._sce_lgtcaygl(s);
            console.log(`_sce_lgtcaygl("${s}") =`, JSON.stringify(result));
        } catch (e) {
            console.log(`_sce_lgtcaygl("${s}") error:`, e.message);
        }
    }
}

// Debug _sce_dlgtqred
console.log('\n=== Debug _sce_dlgtqred ===');
if (typeof context._sce_dlgtqred === 'function') {
    console.log('_sce_dlgtqred source:', context._sce_dlgtqred.toString().substring(0, 1000));

    // Test with various parameter combinations
    const tests = [
        [R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY],
        ["xWrtQpP4Z4RsrRCY", ENCRYPTR_SERVER, COPYRIGHT_KEY],
        [R1_RANDOM, COPYRIGHT_KEY, ENCRYPTR_SERVER],
    ];

    for (const [r1, ers, ck] of tests) {
        try {
            const result = context._sce_dlgtqred(r1, ers, ck);
            console.log(`\n_sce_dlgtqred("${r1}", "${ers}", "${ck}"):`);
            console.log('  typeof:', typeof result);

            if (typeof result === 'string') {
                console.log('  string:', result);
                console.log('  hex:', Buffer.from(result, 'binary').toString('hex'));
                // Try base64 decode
                try {
                    const decoded = Buffer.from(result, 'base64');
                    console.log('  b64decoded:', decoded.toString('hex'), `(${decoded.length}B)`);
                } catch(e) {}
            } else if (Array.isArray(result) || (result && result.length !== undefined)) {
                let hex = '';
                let allNums = true;
                for (let i = 0; i < result.length; i++) {
                    const v = result[i];
                    if (typeof v === 'number') {
                        hex += (v & 0xFF).toString(16).padStart(2, '0');
                    } else if (typeof v === 'string') {
                        hex += (v.charCodeAt(0) & 0xFF).toString(16).padStart(2, '0');
                    } else {
                        allNums = false;
                        hex += '??';
                    }
                }
                console.log('  length:', result.length);
                console.log('  hex:', hex);
                console.log('  allNums:', allNums);
                console.log('  values:', JSON.stringify(Array.from(result)));
            }
        } catch (e) {
            console.log(`_sce_dlgtqred error:`, e.message);
        }
    }
}

// Also check: maybe the return value of _sce_dlgtqred should be passed through coerceArray
console.log('\n=== Checking coerceArray behavior ===');
// The coerceArray function is part of the AES class (class A/s)
// Let's try to find it in the context
for (const key of Object.keys(context)) {
    if (typeof context[key] === 'function' && key.toLowerCase().includes('coerce')) {
        console.log('Found coerce function:', key);
    }
}
