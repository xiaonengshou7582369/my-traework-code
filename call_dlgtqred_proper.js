// Properly call _sce_dlgtqred with correct base64 string arguments
const fs = require('fs');
const vm = require('vm');
const crypto = require('crypto');

// DRM parameters (base64 strings, as passed in the actual Youku player)
const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";  // upsParams.R1
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";  // encryptRServer
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";  // copyrightKey

const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";

// Set up browser environment
const context = {
    console: { log(){}, error(){}, warn(){}, debug(){}, info(){} },
    navigator: { 
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 
        platform: 'Win32', 
        language: 'zh-CN',
        canPlayType: () => '',
        appName: 'Netscape',
        appVersion: '5.0',
        cookieEnabled: true,
        plugins: { length: 0 },
        mimeTypes: { length: 0 },
    },
    document: { 
        createElement: () => ({setAttribute(){},appendChild(){},style:{},getContext:()=>null,addEventListener(){},removeAttribute(){},innerHTML:''}), 
        getElementsByTagName: () => [{appendChild(){},addEventListener(){}}], 
        getElementById: () => null, 
        body: {appendChild(){},addEventListener(){}}, 
        head: {appendChild(){}}, 
        addEventListener(){}, removeEventListener(){}, 
        cookie:'', referrer:'', title:'', URL:'https://www.youku.com/', 
        domain:'youku.com', documentElement:{style:{}} 
    },
    location: { 
        href: 'https://www.youku.com/', 
        hostname: 'www.youku.com', 
        protocol: 'https:', 
        pathname: '/', 
        search: '', 
        hash: '', 
        origin: 'https://www.youku.com',
        host: 'www.youku.com',
        port: '',
        toString: () => 'https://www.youku.com/',
    },
    localStorage: { getItem: () => null, setItem(){}, removeItem(){}, clear(){} },
    sessionStorage: { getItem: () => null, setItem(){}, removeItem(){}, clear(){} },
    performance: { now: () => Date.now(), timing: { navigationStart: 0 }, getEntries: () => [] },
    screen: { width: 1920, height: 1080, colorDepth: 24, pixelDepth: 24 },
    history: { pushState(){}, replaceState(){}, back(){}, forward(){}, go(){} },
    setTimeout: (fn, ms) => { 
        // For synchronous execution, run immediately if ms=0
        if (ms === 0 || !ms) { try { fn(); } catch(e) {} }
        return 0; 
    }, 
    clearTimeout(){}, 
    setInterval: () => 0, 
    clearInterval(){},
    setImmediate: (fn) => { try { fn(); } catch(e) {} return 0; },
    clearImmediate(){},
    requestAnimationFrame: (fn) => { try { fn(); } catch(e) {} return 0; },
    cancelAnimationFrame(){},
    btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
    atob: (s) => Buffer.from(s, 'base64').toString('binary'),
    escape, unescape, 
    decodeURIComponent, encodeURIComponent, encodeURI, decodeURI,
    parseInt, parseFloat, isNaN, isFinite, NaN, Infinity, undefined,
    Date, Math, JSON, Array, Object, String, Number, Boolean, Function,
    RegExp, Error, TypeError, RangeError, SyntaxError, ReferenceError, URIError, EvalError,
    Uint8Array, Uint16Array, Uint32Array, Int8Array, Int16Array, Int32Array,
    Float32Array, Float64Array, ArrayBuffer, DataView, SharedArrayBuffer,
    TextEncoder, TextDecoder, Map, Set, WeakMap, WeakSet,
    Promise, Symbol, Proxy, Reflect, BigInt,
    Image: function(){}, 
    XMLHttpRequest: function(){ this.open = function(){}; this.send = function(){}; this.setRequestHeader = function(){}; this.getAllResponseHeaders = () => ''; },
    URL, URLSearchParams, Intl,
    WebKitMediaKeys: function(){ this.isTypeSupported = () => false; },
    MediaSource: function(){ this.isTypeSupported = () => false; },
    Request: function(){},
    Response: function(){},
    Headers: function(){},
    fetch: () => Promise.reject(new Error('no network')),
    WebSocket: function(){ this.send = function(){}; this.close = function(){}; },
    Worker: function(){ this.postMessage = function(){}; this.terminate = function(){}; this.addEventListener = function(){}; },
    Blob: function(){},
    File: function(){},
    FileReader: function(){ this.readAsArrayBuffer = function(){}; this.readAsText = function(){}; },
    Crypto: function(){},
    crypto: crypto.getRandomValues ? { getRandomValues: (arr) => { for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random()*256); return arr; } } : undefined,
    Math,
    eval: eval,
    Buffer: Buffer,
};
context.window = context; 
context.self = context; 
context.global = context; 
context.globalThis = context;
context.top = context;
context.parent = context;
context.frames = context;

vm.createContext(context);

// Load and execute the obfuscated JS
let jsCode = fs.readFileSync(JS_FILE, 'utf-8');
console.log(`JS file loaded: ${jsCode.length} chars`);

// Patch: Replace 'decodeURIComponent(escape(f.stringify(r)))' with 'f.stringify(r)'
// This fixes the UTF-8 conversion issue
jsCode = jsCode.replace(/decodeURIComponent\(escape\(([^)]+)\)\)/g, '$1');

// Also patch any other escape/unescape patterns that might cause issues
// jsCode = jsCode.replace(/escape\(/g, '(').replace(/unescape\(/g, '(');

try {
    vm.runInContext(jsCode, context, { timeout: 30000, filename: 'ykdrm.js' });
    console.log('JS executed successfully');
} catch(e) {
    console.log('JS execution error:', e.message);
}

// Check what functions are available
console.log('\n=== Checking _sce_* functions ===');
console.log('_sce_r_skjhfnck:', typeof context._sce_r_skjhfnck);
console.log('_sce_lgtcaygl:', typeof context._sce_lgtcaygl);
console.log('_sce_dlgtqred:', typeof context._sce_dlgtqred);

// Try calling _sce_dlgtqred with the correct arguments (base64 strings)
if (typeof context._sce_dlgtqred === 'function') {
    console.log('\n=== Calling _sce_dlgtqred(R1Random, encryptRServer, copyrightKey) ===');
    console.log(`Args: "${R1_RANDOM}", "${ENCRYPTR_SERVER}", "${COPYRIGHT_KEY}"`);
    
    try {
        const result = context._sce_dlgtqred(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY);
        console.log(`Result type: ${typeof result}`);
        console.log(`Result value: ${result}`);
        
        if (typeof result === 'string') {
            // Try as base64
            try {
                const decoded = Buffer.from(result, 'base64');
                console.log(`Base64 decoded: ${decoded.toString('hex')} (${decoded.length}B)`);
            } catch(e) {}
            // Try as hex
            try {
                const hexDecoded = Buffer.from(result, 'hex');
                console.log(`Hex decoded: ${hexDecoded.toString('hex')} (${hexDecoded.length}B)`);
            } catch(e) {}
            // Try as ASCII bytes
            const asciiBytes = Buffer.from(result, 'ascii');
            console.log(`ASCII bytes: ${asciiBytes.toString('hex')} (${asciiBytes.length}B)`);
        } else if (result && typeof result === 'object') {
            // Check if it's an array/typedarray
            if (result.length !== undefined) {
                console.log(`Array length: ${result.length}`);
                const arr = Array.from(result);
                console.log(`Array values: ${arr.map(b => b.toString(16).padStart(2, '0')).join('')}`);
                console.log(`Array values (dec): ${arr.join(', ')}`);
                
                // If it's 16 bytes, it's a valid AES-128 key
                if (result.length === 16 || result.length === 24 || result.length === 32) {
                    const key = Buffer.from(result);
                    console.log(`\n*** Valid AES key! ***`);
                    console.log(`Key (hex): ${key.toString('hex')}`);
                    console.log(`Key (base64): ${key.toString('base64')}`);
                }
            } else {
                console.log(`Object: ${JSON.stringify(result).substring(0, 500)}`);
            }
        }
    } catch(e) {
        console.log(`Error calling _sce_dlgtqred: ${e.message}`);
        console.log(`Stack: ${e.stack}`);
    }
}

// Also try: what if we need to call _sce_r_skjhfnck first to set up R1?
if (typeof context._sce_r_skjhfnck === 'function') {
    console.log('\n=== Testing _sce_r_skjhfnck() ===');
    try {
        const r = context._sce_r_skjhfnck();
        console.log(`_sce_r_skjhfnck(): "${r}" (${typeof r}, len=${r ? r.length : 0})`);
        
        // Try _sce_lgtcaygl with R1Random
        if (typeof context._sce_lgtcaygl === 'function') {
            const lgtc1 = context._sce_lgtcaygl(R1_RANDOM);
            console.log(`_sce_lgtcaygl(R1Random): "${lgtc1}" (${typeof lgtc1})`);
            
            // Try _sce_lgtcaygl with the r from _sce_r_skjhfnck
            const lgtc2 = context._sce_lgtcaygl(r);
            console.log(`_sce_lgtcaygl(r_random): "${lgtc2}" (${typeof lgtc2})`);
        }
    } catch(e) {
        console.log(`Error: ${e.message}`);
    }
}

// Try: maybe _sce_dlgtqred needs the result of _sce_lgtcaygl as first arg?
if (typeof context._sce_lgtcaygl === 'function' && typeof context._sce_dlgtqred === 'function') {
    console.log('\n=== Trying _sce_dlgtqred with _sce_lgtcaygl(R1) as first arg ===');
    const encryptR1 = context._sce_lgtcaygl(R1_RANDOM);
    console.log(`encryptR1 = _sce_lgtcaygl(R1Random) = "${encryptR1}"`);
    try {
        const result = context._sce_dlgtqred(encryptR1, ENCRYPTR_SERVER, COPYRIGHT_KEY);
        console.log(`Result: ${result} (${typeof result})`);
        if (typeof result === 'string') {
            try {
                const decoded = Buffer.from(result, 'base64');
                console.log(`Base64 decoded: ${decoded.toString('hex')} (${decoded.length}B)`);
            } catch(e) {}
        }
    } catch(e) {
        console.log(`Error: ${e.message}`);
    }
}
