// derive_key_node.js - Run Youku DRM JS in Node.js to derive decryption key
const fs = require('fs');
const path = require('path');
const vm = require('vm');

// DRM parameters from episode 1
const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";

const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";

// Create a browser-like context
const context = {
    window: {},
    self: {},
    global: {},
    navigator: {
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        platform: 'Win32',
        language: 'zh-CN',
        canPlayType: function() { return ''; },
        plugins: [],
        mimeTypes: [],
    },
    document: {
        createElement: function() {
            return {
                setAttribute: function() {},
                appendChild: function() {},
                style: {},
                getContext: function() { return null; },
                addEventListener: function() {},
                removeEventListener: function() {},
                innerHTML: '',
                src: '',
            };
        },
        getElementsByTagName: function() {
            return [{ appendChild: function() {}, addEventListener: function() {} }];
        },
        getElementById: function() { return null; },
        body: { appendChild: function() {}, addEventListener: function() {} },
        head: { appendChild: function() {} },
        addEventListener: function() {},
        removeEventListener: function() {},
        cookie: '',
        referrer: '',
        title: '',
        URL: 'https://www.youku.com/',
        domain: 'youku.com',
        documentElement: { style: {} },
    },
    location: {
        href: 'https://www.youku.com/',
        hostname: 'www.youku.com',
        protocol: 'https:',
        pathname: '/',
        search: '',
        hash: '',
        origin: 'https://www.youku.com',
    },
    localStorage: {
        getItem: function() { return null; },
        setItem: function() {},
        removeItem: function() {},
        clear: function() {},
        key: function() { return null; },
        length: 0,
    },
    sessionStorage: {
        getItem: function() { return null; },
        setItem: function() {},
        removeItem: function() {},
        clear: function() {},
        key: function() { return null; },
        length: 0,
    },
    performance: {
        now: function() { return Date.now(); },
        timing: { navigationStart: 0 },
        getEntries: function() { return []; },
    },
    screen: { width: 1920, height: 1080 },
    history: { pushState: function() {}, replaceState: function() {}, back: function() {}, forward: function() {}, go: function() {} },
    btoa: function(s) {
        return Buffer.from(s, 'binary').toString('base64');
    },
    atob: function(s) {
        return Buffer.from(s, 'base64').toString('binary');
    },
    escape: escape,
    unescape: unescape,
    decodeURIComponent: decodeURIComponent,
    encodeURIComponent: encodeURIComponent,
    encodeURI: encodeURI,
    decodeURI: decodeURI,
    parseInt: parseInt,
    parseFloat: parseFloat,
    isNaN: isNaN,
    isFinite: isFinite,
    setTimeout: function(fn, ms) { return 0; },
    clearTimeout: function() {},
    setInterval: function(fn, ms) { return 0; },
    clearInterval: function() {},
    Date: Date,
    Math: Math,
    JSON: JSON,
    Array: Array,
    Object: Object,
    String: String,
    Number: Number,
    Boolean: Boolean,
    RegExp: RegExp,
    Error: Error,
    TypeError: TypeError,
    RangeError: RangeError,
    SyntaxError: SyntaxError,
    ReferenceError: ReferenceError,
    Uint8Array: Uint8Array,
    Uint16Array: Uint16Array,
    Uint32Array: Uint32Array,
    Int8Array: Int8Array,
    Int16Array: Int16Array,
    Int32Array: Int32Array,
    Float32Array: Float32Array,
    Float64Array: Float64Array,
    ArrayBuffer: ArrayBuffer,
    DataView: DataView,
    TextEncoder: TextEncoder,
    TextDecoder: TextDecoder,
    Map: Map,
    Set: Set,
    WeakMap: WeakMap,
    WeakSet: WeakSet,
    Promise: Promise,
    Symbol: Symbol,
    Proxy: Proxy,
    Reflect: Reflect,
    console: { log: function() {}, error: function() {}, warn: function() {}, debug: function() {}, info: function() {}, trace: function() {} },
};

// Make window and self circular references
context.window = context;
context.self = context;
context.global = context;
context.globalThis = context;

// Also add common DOM APIs
context.Image = function() {};
context.XMLHttpRequest = function() {
    this.open = function() {};
    this.send = function() {};
    this.setRequestHeader = function() {};
    this.addEventListener = function() {};
    this.readyState = 4;
    this.status = 200;
    this.responseText = '';
    this.response = '';
};
context.fetch = function() { return Promise.resolve({ json: function() { return Promise.resolve({}); }, text: function() { return Promise.resolve(''); } }); };
context.MessageChannel = function() { this.port1 = { postMessage: function() {} }; this.port2 = { onmessage: null }; };
context.crypto = {
    getRandomValues: function(arr) {
        for (let i = 0; i < arr.length; i++) {
            arr[i] = Math.floor(Math.random() * 256);
        }
        return arr;
    },
    subtle: {},
};
context.URL = URL;
context.URLSearchParams = URLSearchParams;

// Create VM context
vm.createContext(context);

// Read the DRM JS file
const jsCode = fs.readFileSync(JS_FILE, 'utf-8');

// Patch the UTF-8 stringify function
const patchedJs = jsCode.replace(
    'decodeURIComponent(escape(f.stringify(r)))',
    'f.stringify(r)'
);

// Execute the DRM JS in the VM context
try {
    vm.runInContext(patchedJs, context, { filename: '904ddb4d.js', timeout: 30000 });
    console.log('DRM JS loaded successfully');
} catch (e) {
    console.log('DRM JS load error:', e.message);
    // Try without patch
    try {
        vm.runInContext(jsCode, context, { filename: '904ddb4d.js', timeout: 30000 });
        console.log('DRM JS loaded (unpatched)');
    } catch (e2) {
        console.log('DRM JS load error (unpatched):', e2.message);
    }
}

// Check if _sce_dlgtqred is defined
console.log('_sce_dlgtqred type:', typeof context._sce_dlgtqred);
console.log('_sce_r_skjhfnck type:', typeof context._sce_r_skjhfnck);
console.log('_sce_lgtcaygl type:', typeof context._sce_lgtcaygl);
console.log('str16ToBytes type:', typeof context.str16ToBytes);

// If _sce_dlgtqred is available, call it
if (typeof context._sce_dlgtqred === 'function') {
    try {
        const result = context._sce_dlgtqred(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY);
        console.log('\n_sce_dlgtqred result:');
        console.log('  typeof:', typeof result);
        console.log('  constructor:', result && result.constructor ? result.constructor.name : 'unknown');
        console.log('  length:', result && result.length !== undefined ? result.length : -1);

        if (typeof result === 'string') {
            console.log('  string value:', result);
            console.log('  hex:', Buffer.from(result, 'binary').toString('hex'));
        } else if (result && result.length !== undefined) {
            let hex = '';
            for (let i = 0; i < result.length; i++) {
                let v = result[i];
                if (typeof v === 'number') {
                    hex += (v & 0xFF).toString(16).padStart(2, '0');
                } else if (typeof v === 'string') {
                    hex += (v.charCodeAt(0) & 0xFF).toString(16).padStart(2, '0');
                }
            }
            console.log('  hex:', hex);
            console.log('  bytes:', hex.length / 2);

            // Try base64 decode
            try {
                const b64decoded = Buffer.from(result.map(c => String.fromCharCode(c)).join(''), 'binary').toString('base64');
                console.log('  base64:', b64decoded);
            } catch(e) {}
        } else if (result && result.buffer) {
            const view = new Uint8Array(result.buffer);
            let hex = '';
            for (let i = 0; i < view.length; i++) {
                hex += view[i].toString(16).padStart(2, '0');
            }
            console.log('  buffer hex:', hex);
        }
    } catch (e) {
        console.log('_sce_dlgtqred call error:', e.message);
        console.log('  stack:', e.stack ? e.stack.substring(0, 500) : '');
    }
} else {
    console.log('\n_sce_dlgtqred not found. Trying window._sce_dlgtqred...');
    if (typeof context.window._sce_dlgtqred === 'function') {
        console.log('Found window._sce_dlgtqred!');
    } else {
        console.log('Not found. Checking all _sce_ properties...');
        for (const key of Object.keys(context).filter(k => k.includes('_sce_'))) {
            console.log(`  ${key}: ${typeof context[key]}`);
        }
        // Also check window
        if (context.window) {
            for (const key of Object.keys(context.window).filter(k => k.includes('_sce_'))) {
                console.log(`  window.${key}: ${typeof context.window[key]}`);
            }
        }
    }
}

// Also try str16ToBytes if available
if (typeof context.str16ToBytes === 'function') {
    try {
        const result = context.str16ToBytes(R1_RANDOM);
        console.log('\nstr16ToBytes result:', result);
    } catch (e) {
        console.log('str16ToBytes error:', e.message);
    }
}

// Try _sce_r_skjhfnck
if (typeof context._sce_r_skjhfnck === 'function') {
    try {
        const result = context._sce_r_skjhfnck(R1_RANDOM);
        console.log('\n_sce_r_skjhfnck result:', result);
    } catch (e) {
        console.log('_sce_r_skjhfnck error:', e.message);
    }
}

// Try _sce_lgtcaygl
if (typeof context._sce_lgtcaygl === 'function') {
    try {
        const result = context._sce_lgtcaygl(R1_RANDOM);
        console.log('\n_sce_lgtcaygl result:', result);
    } catch (e) {
        console.log('_sce_lgtcaygl error:', e.message);
    }
}
