// try_window_global.js - Try with window = global set before DRM JS load
// This simulates the browser environment where window._sce_dlgtqred is called

// Set up global browser environment
global.window = global;  // KEY: set window = global so window._sce_dlgtqred works

global.navigator = {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
    platform: 'Win32',
    language: 'zh-CN',
    canPlayType: function() { return ''; },
    plugins: { length: 0 },
    appVersion: '5.0',
};
global.document = {
    createElement: function() {
        return {
            setAttribute: function(){},
            appendChild: function(){},
            style: {},
            getContext: function() { return null; },
            addEventListener: function(){},
            innerHTML: '',
        };
    },
    getElementsByTagName: function() {
        return [{ appendChild: function(){}, addEventListener: function(){} }];
    },
    getElementById: function() { return null; },
    body: { appendChild: function(){}, addEventListener: function(){} },
    head: { appendChild: function(){} },
    addEventListener: function(){},
    removeEventListener: function(){},
    cookie: '',
    referrer: '',
    title: '',
    URL: 'https://www.youku.com/',
    domain: 'youku.com',
    documentElement: { style: {} },
};
global.location = {
    href: 'https://www.youku.com/',
    hostname: 'www.youku.com',
    protocol: 'https:',
    pathname: '/',
    search: '',
    hash: '',
    origin: 'https://www.youku.com',
};
global.localStorage = {
    getItem: function() { return null; },
    setItem: function(){},
    removeItem: function(){},
};
global.sessionStorage = {
    getItem: function() { return null; },
    setItem: function(){},
    removeItem: function(){},
};
global.screen = { width: 1920, height: 1080 };
global.performance = { now: function() { return Date.now(); }, timing: { navigationStart: 0 } };
global.btoa = function(s) { return Buffer.from(s, 'binary').toString('base64'); };
global.atob = function(s) { return Buffer.from(s, 'base64').toString('binary'); };
global.decodeURIComponent = function(s) {
    s = s.replace(/%u([0-9A-Fa-f]{4})/g, function(_, p) {
        return String.fromCharCode(parseInt(p, 16));
    });
    var bytes = [];
    var i = 0;
    while (i < s.length) {
        if (s[i] === '%' && i + 2 < s.length) {
            var hex = s.substr(i + 1, 2);
            if (/^[0-9A-Fa-f]{2}$/.test(hex)) {
                bytes.push(parseInt(hex, 16));
                i += 3;
                continue;
            }
        }
        bytes.push(s.charCodeAt(i));
        i++;
    }
    return String.fromCharCode.apply(null, bytes);
};

// Load DRM JS
const fs = require('fs');
const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";
let jsCode = fs.readFileSync(JS_FILE, 'utf-8');
jsCode = jsCode.replace(/decodeURIComponent\s*\(\s*escape\s*\(([^)]+)\)\s*\)/g, 'unescape($1)');

console.log('Loading DRM JS with window=global...');
try {
    eval(jsCode);
    console.log('DRM JS loaded successfully');
} catch(e) {
    console.log('Error loading:', e.message);
}

// Check if _sce_dlgtqred is on window
console.log('\n=== Checking function availability ===');
console.log('typeof window._sce_dlgtqred:', typeof window._sce_dlgtqred);
console.log('typeof _sce_dlgtqred:', typeof _sce_dlgtqred);
console.log('window === global:', window === global);

const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";

// Call via window._sce_dlgtqred (like the real player does)
console.log('\n=== Calling window._sce_dlgtqred ===');
try {
    var result = window._sce_dlgtqred(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY);
    console.log('typeof:', typeof result);
    console.log('constructor:', result.constructor.name);
    console.log('length:', result.length);
    console.log('values:', Array.from(result));
    console.log('hex:', Buffer.from(Array.from(result)).toString('hex'));
    
    // Check if it's different now
    if (result.length === 16) {
        console.log('\n*** 16 bytes! Valid AES key! ***');
        var key = Buffer.from(Array.from(result));
        console.log('Key hex:', key.toString('hex'));
    } else if (result.length === 24) {
        console.log('\n*** 24 bytes! Valid AES-192 key! ***');
    } else if (result.length === 32) {
        console.log('\n*** 32 bytes! Valid AES-256 key! ***');
    } else {
        console.log('\n*** Still ' + result.length + ' bytes - not a valid AES key size ***');
    }
} catch(e) {
    console.log('Error:', e.message);
    console.log(e.stack);
}

// Also try _sce_lgtcaygl via window
console.log('\n=== Calling window._sce_lgtcaygl ===');
try {
    var result2 = window._sce_lgtcaygl(R1_RANDOM);
    console.log('value:', result2);
    if (typeof result2 === 'string') {
        var dec = Buffer.from(result2, 'base64');
        console.log('decoded hex:', dec.toString('hex'));
        console.log('decoded length:', dec.length);
    }
} catch(e) {
    console.log('Error:', e.message);
}
