// explore_sesca.js - Deep exploration of the sesca cipher and kdf
const fs = require('fs');
const vm = require('vm');
const crypto = require('crypto');

const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";
const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";

// Sandbox
const sandbox = {
    navigator: { userAgent: 'Mozilla/5.0', platform: 'Win32', language: 'zh-CN', canPlayType: () => '', plugins: { length: 0 }, appVersion: '5.0' },
    document: { createElement: () => ({ setAttribute(){}, appendChild(){}, style: {}, getContext: () => null, addEventListener(){} }), getElementsByTagName: () => [{ appendChild(){}, addEventListener(){} }], getElementById: () => null, body: { appendChild(){}, addEventListener(){} }, head: { appendChild(){} }, addEventListener(){}, removeEventListener(){}, cookie: '', referrer: '', title: '', URL: 'https://www.youku.com/', domain: 'youku.com', documentElement: { style: {} } },
    location: { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:', pathname: '/', search: '', hash: '', origin: 'https://www.youku.com' },
    localStorage: { getItem: () => null, setItem(){}, removeItem(){} },
    sessionStorage: { getItem: () => null, setItem(){}, removeItem(){} },
    screen: { width: 1920, height: 1080 },
    performance: { now: () => Date.now(), timing: { navigationStart: 0 } },
    btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
    atob: (s) => Buffer.from(s, 'base64').toString('binary'),
    setTimeout, setInterval, clearTimeout, clearInterval,
    console, Math, Date, parseInt, parseFloat, isNaN,
    String, Number, Boolean, Array, Object, JSON, RegExp, Error, TypeError, RangeError,
    encodeURIComponent, escape, unescape,
};
sandbox.decodeURIComponent = function(s) {
    s = s.replace(/%u([0-9A-Fa-f]{4})/g, (_, p) => String.fromCharCode(parseInt(p, 16)));
    var bytes = [];
    for (var i = 0; i < s.length;) {
        if (s[i] === '%' && i + 2 < s.length && /^[0-9A-Fa-f]{2}$/.test(s.substr(i+1, 2))) {
            bytes.push(parseInt(s.substr(i+1, 2), 16)); i += 3;
        } else { bytes.push(s.charCodeAt(i)); i++; }
    }
    return String.fromCharCode.apply(null, bytes);
};
sandbox.global = sandbox;
sandbox.window = sandbox;

let jsCode = fs.readFileSync(JS_FILE, 'utf-8');
jsCode = jsCode.replace(/decodeURIComponent\s*\(\s*escape\s*\(([^)]+)\)\s*\)/g, 'unescape($1)');
vm.createContext(sandbox);
vm.runInContext(jsCode, sandbox, { filename: 'drm.js' });

const lib = sandbox._Cc_S_drskf_usiunsn_;
console.log('=== Top-level lib keys ===');
console.log(Object.keys(lib).join(', '));

// === Explore sesca ===
console.log('\n=== sesca structure ===');
const sesca = lib.sesca;
console.log('Type:', typeof sesca);
console.log('Keys:', Object.keys(sesca).join(', '));

for (const key of Object.keys(sesca)) {
    const v = sesca[key];
    console.log(`\nsesca.${key}:`);
    console.log('  type:', typeof v);
    if (typeof v === 'function') {
        console.log('  length (args):', v.length);
        console.log('  source (first 500):', v.toString().substring(0, 500));
    } else if (typeof v === 'object' && v !== null) {
        console.log('  keys:', Object.keys(v).join(', '));
    } else {
        console.log('  value:', v);
    }
}

// === Explore kdf ===
console.log('\n=== kdf structure ===');
const kdf = lib.kdf;
console.log('Type:', typeof kdf);
console.log('Keys:', Object.keys(kdf).join(', '));

for (const key of Object.keys(kdf)) {
    const v = kdf[key];
    console.log(`\nkdf.${key}:`);
    console.log('  type:', typeof v);
    if (typeof v === 'function') {
        console.log('  length (args):', v.length);
        console.log('  source (first 500):', v.toString().substring(0, 500));
    } else if (typeof v === 'object' && v !== null) {
        console.log('  keys:', Object.keys(v).join(', '));
    } else {
        console.log('  value:', v);
    }
}

// === Explore algo ===
console.log('\n=== algo structure ===');
const algo = lib.algo;
console.log('Keys:', Object.keys(algo).join(', '));

for (const key of Object.keys(algo)) {
    const v = algo[key];
    console.log(`\nalgo.${key}:`);
    console.log('  type:', typeof v);
    if (typeof v === 'function') {
        console.log('  length (args):', v.length);
    } else if (typeof v === 'object' && v !== null) {
        console.log('  keys:', Object.keys(v).join(', '));
        // Try to see methods
        for (const m of Object.keys(v)) {
            const mv = v[m];
            if (typeof mv === 'function') {
                console.log(`    ${m}: function (args=${mv.length})`);
            } else {
                console.log(`    ${m}: ${typeof mv} = ${mv}`);
            }
        }
    }
}

// === Explore lib.lib (CryptoJS-style) ===
console.log('\n=== lib.lib structure ===');
if (lib.lib) {
    console.log('Keys:', Object.keys(lib.lib).join(', '));
    for (const key of Object.keys(lib.lib)) {
        const v = lib.lib[key];
        if (typeof v === 'object' && v !== null) {
            console.log(`  lib.${key}: keys=${Object.keys(v).join(', ')}`);
        } else {
            console.log(`  lib.${key}: ${typeof v}`);
        }
    }
}

// === Look at the 18-byte dlgtqred result more carefully ===
console.log('\n=== Re-examining _sce_dlgtqred ===');
const result = sandbox._sce_dlgtqred(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY);
console.log('Result:', JSON.stringify(result));
console.log('Type:', typeof result, 'IsArray:', Array.isArray(result));
console.log('Length:', result.length);

// Check if it's actually a WordArray.words (32-bit integers)
// If so, 18 words × 4 bytes = 72 bytes
if (lib.lib && lib.lib.WordArray) {
    const WA = lib.lib.WordArray;
    console.log('\nWordArray create test:');
    try {
        // Treat the 18 values as 32-bit words
        const wa = WA.create(result, result.length * 4);
        console.log('Created WA with sigBytes:', wa.sigBytes);
        // Convert to bytes
        const bytes = [];
        for (let i = 0; i < wa.sigBytes; i++) {
            bytes.push((wa.words[i >>> 2] >>> (24 - (i % 4) * 8)) & 0xff);
        }
        console.log('As bytes (72B):', Buffer.from(bytes).toString('hex'));
    } catch(e) { console.log('Error:', e.message); }
}

// === Check encrypt/decrypt with sesca ===
console.log('\n=== Trying sesca decrypt ===');
const r1Bytes = Buffer.from(R1_RANDOM, 'base64');
const encServerBytes = Buffer.from(ENCRYPTR_SERVER, 'base64');
const cpyKeyBytes = Buffer.from(COPYRIGHT_KEY, 'base64');
console.log('R1:', r1Bytes.toString('hex'), `(${r1Bytes.length}B)`);
console.log('encServer:', encServerBytes.toString('hex'), `(${encServerBytes.length}B)`);
console.log('cpyKey:', cpyKeyBytes.toString('hex'), `(${cpyKeyBytes.length}B)`);

// Convert bytes to words (big-endian, like CryptoJS)
function bytesToWords(bytes) {
    const words = [];
    for (let i = 0; i < bytes.length; i += 4) {
        const w = (bytes[i] << 24) | ((bytes[i+1] || 0) << 16) | ((bytes[i+2] || 0) << 8) | (bytes[i+3] || 0);
        words.push(w >>> 0);
    }
    return words;
}

// Convert words to bytes
function wordsToBytes(words, sigBytes) {
    const bytes = [];
    for (let i = 0; i < sigBytes; i++) {
        bytes.push((words[i >>> 2] >>> (24 - (i % 4) * 8)) & 0xff);
    }
    return bytes;
}

// Make WordArray-like objects
const r1WA = { words: bytesToWords(r1Bytes), sigBytes: r1Bytes.length };
const encServerWA = { words: bytesToWords(encServerBytes), sigBytes: encServerBytes.length };
const cpyKeyWA = { words: bytesToWords(cpyKeyBytes), sigBytes: cpyKeyBytes.length };

console.log('R1 WA:', JSON.stringify(r1WA));
console.log('encServer WA:', JSON.stringify(encServerWA));
console.log('cpyKey WA:', JSON.stringify(cpyKeyWA));

// Try sesca.algt (encrypt) and sesca.lgt (decrypt?) with various data
console.log('\n--- Trying sesca.lgt (decrypt?) ---');
const testData = bytesToWords(encServerBytes);
const testKey = bytesToWords(r1Bytes);

// Try different signatures
const argSets = [
    ['key_data', [testKey, testData]],
    ['data_key', [testData, testKey]],
];

for (const [label, args] of argSets) {
    console.log(`\n  ${label}:`);
    // Make copies
    const a1 = args[0].slice();
    const a2 = args[1].slice();
    try {
        const ret = sesca.lgt(a1, a2);
        console.log('  Return:', ret);
        console.log('  a1 after:', JSON.stringify(a1));
        console.log('  a2 after:', JSON.stringify(a2));
        if (Array.isArray(a1) && JSON.stringify(a1) !== JSON.stringify(args[0])) {
            const bytes = wordsToBytes(a1, a1.length * 4);
            console.log('  a1 as bytes:', Buffer.from(bytes).toString('hex'));
        }
        if (Array.isArray(a2) && JSON.stringify(a2) !== JSON.stringify(args[1])) {
            const bytes = wordsToBytes(a2, a2.length * 4);
            console.log('  a2 as bytes:', Buffer.from(bytes).toString('hex'));
        }
    } catch(e) { console.log('  Error:', e.message); }
}

// === Try kdf.aasdefcp ===
console.log('\n=== Trying kdf.aasdefcp ===');
if (typeof kdf.aasdefcp === 'function') {
    // Try various signatures
    const tries = [
        ['r1', [r1WA]],
        ['r1_encServer', [r1WA, encServerWA]],
        ['r1_encServer_cpyKey', [r1WA, encServerWA, cpyKeyWA]],
    ];
    for (const [label, args] of tries) {
        console.log(`\n  ${label}:`);
        try {
            const ret = kdf.aasdefcp(...args);
            console.log('  Return type:', typeof ret);
            if (ret && ret.words) {
                console.log('  WordArray! sigBytes:', ret.sigBytes);
                const bytes = wordsToBytes(ret.words, ret.sigBytes);
                console.log('  bytes:', Buffer.from(bytes).toString('hex'));
            } else if (Array.isArray(ret)) {
                console.log('  Array:', JSON.stringify(ret.slice(0, 20)));
            } else if (typeof ret === 'string') {
                console.log('  String:', ret);
            } else {
                console.log('  Value:', ret);
            }
        } catch(e) { console.log('  Error:', e.message); }
    }
}

// === Check the enc encoders ===
console.log('\n=== Checking enc encoders ===');
for (const name of Object.keys(lib.enc)) {
    const enc = lib.enc[name];
    console.log(`\nenc.${name}:`);
    if (typeof enc === 'object' && enc !== null) {
        for (const m of Object.keys(enc)) {
            const mv = enc[m];
            if (typeof mv === 'function') {
                console.log(`  ${m}: function (args=${mv.length})`);
                // Try parsing the 18-byte result
                if (m === 'parse' && typeof mv === 'function') {
                    try {
                        const hexStr = Buffer.from(result).toString('hex');
                        const r = mv(hexStr);
                        console.log(`    parse(hex) = `, r);
                        if (r && r.words) {
                            console.log(`    WordArray sigBytes:`, r.sigBytes);
                        }
                    } catch(e) { console.log(`    parse error:`, e.message); }
                }
            } else {
                console.log(`  ${m}: ${typeof mv}`);
            }
        }
    }
}
