// node_key_derive.js - Derive Youku copyrightDRM key using Node.js
const fs = require('fs');
const vm = require('vm');
const crypto = require('crypto');

const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";
const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";

// Create a browser-like context
const context = {
    console: { log: (...a) => {}, error: (...a) => {}, warn: (...a) => {}, debug: (...a) => {}, info: (...a) => {} },
    navigator: {
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        platform: 'Win32', language: 'zh-CN',
        canPlayType: () => '', plugins: { length: 0 }, mimeTypes: { length: 0 },
    },
    document: {
        createElement: () => ({ setAttribute(){}, appendChild(){}, style: {}, getContext: () => null, addEventListener(){} }),
        getElementsByTagName: () => [{ appendChild(){}, addEventListener(){} }],
        getElementById: () => null,
        body: { appendChild(){}, addEventListener(){} },
        head: { appendChild(){} },
        addEventListener(){}, removeEventListener(){},
        cookie: '', referrer: '', title: '', URL: 'https://www.youku.com/', domain: 'youku.com',
        documentElement: { style: {} },
    },
    location: { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:', pathname: '/', search: '', hash: '', origin: 'https://www.youku.com' },
    localStorage: { getItem: () => null, setItem(){}, removeItem(){} },
    sessionStorage: { getItem: () => null, setItem(){}, removeItem(){} },
    performance: { now: () => Date.now(), timing: { navigationStart: 0 }, getEntries: () => [] },
    screen: { width: 1920, height: 1080 },
    history: { pushState(){}, replaceState(){}, back(){}, forward(){}, go(){} },
    setTimeout: (fn) => { try { fn(); } catch(e) {} return 0; },
    clearTimeout(){}, setInterval: () => 0, clearInterval(){},
    // Use Node.js native functions
    btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
    atob: (s) => Buffer.from(s, 'base64').toString('binary'),
    escape: escape, unescape: unescape,
    decodeURIComponent, encodeURIComponent, encodeURI, decodeURI,
    parseInt, parseFloat, isNaN, isFinite,
    Date, Math, JSON, Array, Object, String, Number, Boolean,
    RegExp, Error, TypeError, RangeError, SyntaxError, ReferenceError,
    Uint8Array, Uint16Array, Uint32Array, Int8Array, Int16Array, Int32Array,
    Float32Array, Float64Array, ArrayBuffer, DataView,
    TextEncoder, TextDecoder, Map, Set, WeakMap, WeakSet,
    Promise, Symbol, Proxy, Reflect,
    Image: function(){}, XMLHttpRequest: function(){ this.open = function(){}; this.send = function(){}; },
    URL, URLSearchParams, Intl,
};
context.window = context;
context.self = context;
context.global = context;
context.globalThis = context;

vm.createContext(context);

// Read and patch the JS
let jsCode = fs.readFileSync(JS_FILE, 'utf-8');

// Patch: Fix the UTF-8 stringify issue
jsCode = jsCode.replace(
    'decodeURIComponent(escape(f.stringify(r)))',
    'f.stringify(r)'
);

// Execute
try {
    vm.runInContext(jsCode, context, { filename: 'youku_drm.js', timeout: 30000 });
    console.log('DRM JS loaded successfully');
} catch (e) {
    console.log('DRM JS load error:', e.message);
    process.exit(1);
}

// Test 1: Call _sce_dlgtqred directly
console.log('\n=== _sce_dlgtqred ===');
try {
    const result = context._sce_dlgtqred(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY);
    if (result) {
        console.log('  type:', typeof result);
        console.log('  constructor:', result.constructor ? result.constructor.name : 'unknown');
        console.log('  length:', result.length);

        let hex = '';
        let isString = typeof result === 'string';
        let len = isString ? result.length : (result.length || 0);

        for (let i = 0; i < len; i++) {
            const v = isString ? result.charCodeAt(i) : result[i];
            hex += (typeof v === 'number' ? v : v.charCodeAt(0)).toString(16).padStart(2, '0');
        }
        console.log('  hex:', hex);
        console.log('  values:', Array.from(isString ? result : result).map(c => typeof c === 'number' ? c : c.charCodeAt(0)));

        // Try as string (if it's actually a string)
        if (isString) {
            console.log('  stringValue:', result);
            // Try base64 decode
            try {
                const decoded = Buffer.from(result, 'base64');
                console.log('  b64decoded:', decoded.toString('hex'), `(${decoded.length}B)`);
                if (decoded.length === 16) {
                    testKey(decoded, 'b64decoded');
                }
            } catch(e) {}
        }

        // Try first 16 bytes as key
        const bytes = Buffer.alloc(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = isString ? result.charCodeAt(i) : (typeof result[i] === 'number' ? result[i] : result[i].charCodeAt(0));
        }
        if (len >= 16) testKey(bytes.slice(0, 16), 'first16');
        if (len === 16 || len === 24 || len === 32) testKey(bytes, 'full');
    } else {
        console.log('  result is null/undefined');
    }
} catch (e) {
    console.log('  error:', e.message);
}

// Test 2: _sce_r_skjhfnck (no args)
console.log('\n=== _sce_r_skjhfnck() ===');
try {
    const r = context._sce_r_skjhfnck();
    console.log('  r:', r, '(type:', typeof r, ')');
} catch (e) {
    console.log('  error:', e.message);
}

// Test 3: _sce_lgtcaygl
console.log('\n=== _sce_lgtcaygl ===');
try {
    const r1 = context._sce_lgtcaygl(R1_RANDOM);
    console.log('  lgtcaygl(R1):', r1, '(type:', typeof r1, ')');
    if (typeof r1 === 'string') {
        try {
            const decoded = Buffer.from(r1, 'base64');
            console.log('  b64decoded:', decoded.toString('hex'), `(${decoded.length}B)`);
            if (decoded.length === 16) testKey(decoded, 'lgtcaygl_b64');
        } catch(e) {}
    }
} catch (e) {
    console.log('  error:', e.message);
}

// Test 4: Try the yk.py algorithm with the r from _sce_r_skjhfnck
console.log('\n=== copyrightDRM with derived r ===');
try {
    const r = context._sce_r_skjhfnck();
    if (typeof r === 'string' && r.length === 16) {
        const key_2 = crypto.createDecipheriv('aes-128-ecb', Buffer.from(r, 'ascii'), null);
        const dec1 = Buffer.concat([key_2.update(Buffer.from(ENCRYPTR_SERVER, 'base64')), key_2.final()]);
        console.log('  r:', r);
        console.log('  key_2:', dec1.toString('hex'));

        const cipher2 = crypto.createDecipheriv('aes-128-ecb', dec1, null);
        const dec2 = Buffer.concat([cipher2.update(Buffer.from(COPYRIGHT_KEY, 'base64')), cipher2.final()]);
        console.log('  raw:', dec2.toString('hex'), `(${dec2.length}B)`);
        console.log('  raw as string:', dec2.toString('utf-8'));

        // Try b64 round-trip
        try {
            const b64dec = Buffer.from(dec2.toString('utf-8'), 'base64');
            console.log('  b64decoded:', b64dec.toString('hex'), `(${b64dec.length}B)`);
            if (b64dec.length === 16) testKey(b64dec, 'copyrightDRM_b64');
        } catch(e) {
            console.log('  b64 decode failed:', e.message);
        }

        testKey(dec1, 'key_2');
        if (dec2.length >= 16) testKey(dec2.slice(0, 16), 'raw[:16]');
        if (dec2.length >= 32) testKey(dec2.slice(16, 32), 'raw[16:32]');
    }
} catch (e) {
    console.log('  error:', e.message);
}


function testKey(key, label) {
    // Read first TS segment and extract video PES payload
    const YKV_PATH = "D:\\Youku Files\\download\\沧元图\\第1集 所有妖怪都得死-国语.ykv";
    const YK_HEADER = 34;
    const VIDEO_PID = 0x0100;

    try {
        // Read manifest
        const stats = fs.statSync(YKV_PATH);
        const fd = fs.openSync(YKV_PATH, 'r');
        const trailer = Buffer.alloc(16);
        fs.readSync(fd, trailer, 0, 16, stats.size - 16);
        const trailerStr = trailer.toString('utf-8');
        const manifestLen = parseInt(trailerStr.split('\0')[0].trim());

        const manifestBuf = Buffer.alloc(manifestLen);
        fs.readSync(fd, manifestBuf, 0, manifestLen, stats.size - 16 - manifestLen);
        const manifest = JSON.parse(decodeURIComponent(manifestBuf.toString('utf-8')));

        // Find first TS segment
        const tsSegs = manifest.filter(m => m.name.endsWith('.ts'));
        tsSegs.sort((a, b) => parseInt(a.name) - parseInt(b.name));
        const seg = tsSegs[0];

        // Read segment data
        const segOff = parseInt(seg.offset) + YK_HEADER;
        const segSize = parseInt(seg.size) - YK_HEADER;
        const segData = Buffer.alloc(segSize);
        fs.readSync(fd, segData, 0, segSize, segOff);
        fs.closeSync(fd);

        // Find first video PES payload
        let pesPayload = null;
        const nPackets = Math.floor(segData.length / 188);
        for (let i = 0; i < nPackets; i++) {
            const pkt = segData.slice(i * 188, (i + 1) * 188);
            if (pkt[0] !== 0x47) continue;
            const pid = ((pkt[1] & 0x1F) << 8) | pkt[2];
            const pusi = (pkt[1] >> 6) & 1;
            if (pid === VIDEO_PID && pusi === 1) {
                const afc = (pkt[3] >> 4) & 0x3;
                let ps = 4;
                if (afc === 2 || afc === 3) {
                    ps = 5 + pkt[4];
                }
                const pes = pkt.slice(ps);
                if (pes[0] === 0x00 && pes[1] === 0x00 && pes[2] === 0x01) {
                    const hdrLen = pes[8];
                    pesPayload = pes.slice(9 + hdrLen);
                }
                break;
            }
        }

        if (!pesPayload) {
            console.log(`  ${label}: No PES payload found`);
            return;
        }

        // Decrypt first 16-byte aligned chunk
        const n = Math.floor(pesPayload.length / 16) * 16;
        if (n === 0) {
            console.log(`  ${label}: PES too small`);
            return;
        }

        const decipher = crypto.createDecipheriv('aes-' + (key.length * 8) + '-ecb', key, null);
        const dec = Buffer.concat([decipher.update(pesPayload.slice(0, n)), decipher.final()]);
        const nal4 = countOccurrences(dec, Buffer.from([0, 0, 0, 1]));
        const nal3 = countOccurrences(dec, Buffer.from([0, 0, 1]));
        const match = nal4 > 0 ? ' *** MATCH!' : '';
        console.log(`  ${label} (${key.length}B): nal4=${nal4} nal3=${nal3}${match} first16=${dec.slice(0, 16).toString('hex')}`);

        if (nal4 > 0) {
            console.log(`    KEY FOUND! key=${key.toString('hex')}`);
        }
    } catch (e) {
        console.log(`  ${label}: error: ${e.message}`);
    }
}

function countOccurrences(buf, pattern) {
    let count = 0;
    let idx = 0;
    while ((idx = buf.indexOf(pattern, idx)) !== -1) {
        count++;
        idx += pattern.length;
    }
    return count;
}
