// node_test_keys.js - Test various key candidates with proper AES-ECB
const fs = require('fs');
const vm = require('vm');
const crypto = require('crypto');

const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";
const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";
const YKV_PATH = "D:\\Youku Files\\download\\沧元图\\第1集 所有妖怪都得死-国语.ykv";
const YK_HEADER = 34;
const VIDEO_PID = 0x0100;

// Load YKV segment
const stats = fs.statSync(YKV_PATH);
const fd = fs.openSync(YKV_PATH, 'r');
const trailer = Buffer.alloc(16);
fs.readSync(fd, trailer, 0, 16, stats.size - 16);
const manifestLen = parseInt(trailer.toString('utf-8').split('\0')[0].trim());
const manifestBuf = Buffer.alloc(manifestLen);
fs.readSync(fd, manifestBuf, 0, manifestLen, stats.size - 16 - manifestLen);
const manifest = JSON.parse(decodeURIComponent(manifestBuf.toString('utf-8')));
const tsSegs = manifest.filter(m => m.name.endsWith('.ts'));
tsSegs.sort((a, b) => parseInt(a.name) - parseInt(b.name));
const seg = tsSegs[0];
const segOff = parseInt(seg.offset) + YK_HEADER;
const segSize = parseInt(seg.size) - YK_HEADER;
const segData = Buffer.alloc(segSize);
fs.readSync(fd, segData, 0, segSize, segOff);
fs.closeSync(fd);

// Get first video PES payload
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
        if (afc === 2 || afc === 3) ps = 5 + pkt[4];
        const pes = pkt.slice(ps);
        if (pes[0] === 0x00 && pes[1] === 0x00 && pes[2] === 0x01) {
            pesPayload = pes.slice(9 + pes[8]);
        }
        break;
    }
}
console.log(`PES payload: ${pesPayload.length}B, first16: ${pesPayload.slice(0,16).toString('hex')}`);

// Also get a larger PES payload (multiple packets)
let fullPes = Buffer.alloc(0);
let inPes = false;
for (let i = 0; i < Math.min(nPackets, 50); i++) {
    const pkt = segData.slice(i * 188, (i + 1) * 188);
    if (pkt[0] !== 0x47) continue;
    const pid = ((pkt[1] & 0x1F) << 8) | pkt[2];
    const pusi = (pkt[1] >> 6) & 1;
    if (pid !== VIDEO_PID) continue;
    const afc = (pkt[3] >> 4) & 0x3;
    if (afc === 0 || afc === 2) continue; // no payload
    let ps = 4;
    if (afc === 3) ps = 5 + pkt[4];
    const chunk = pkt.slice(ps);
    if (pusi) {
        if (chunk[0] === 0x00 && chunk[1] === 0x00 && chunk[2] === 0x01) {
            fullPes = chunk.slice(9 + chunk[8]);
        } else {
            fullPes = chunk;
        }
    } else {
        fullPes = Buffer.concat([fullPes, chunk]);
    }
}
console.log(`Full PES (50pkts): ${fullPes.length}B, first16: ${fullPes.slice(0,16).toString('hex')}`);

function testKey(key, label, data) {
    data = data || pesPayload;
    if (key.length !== 16 && key.length !== 24 && key.length !== 32) {
        console.log(`  ${label}: key length ${key.length} not valid`);
        return false;
    }
    const n = Math.floor(data.length / 16) * 16;
    if (n === 0) {
        console.log(`  ${label}: data too small`);
        return false;
    }
    try {
        const decipher = crypto.createDecipheriv('aes-' + (key.length * 8) + '-ecb', key, null);
        decipher.setAutoPadding(false);
        const dec = Buffer.concat([decipher.update(data.slice(0, n)), decipher.final()]);
        const nal4 = countOcc(dec, Buffer.from([0, 0, 0, 1]));
        const nal3 = countOcc(dec, Buffer.from([0, 0, 1]));
        // Check for HEVC NAL types (VPS=32, SPS=33, PPS=34)
        let hevcVps = false;
        for (let i = 0; i < dec.length - 5; i++) {
            if (dec[i]===0 && dec[i+1]===0 && dec[i+2]===0 && dec[i+3]===1) {
                const nalType = (dec[i+4] & 0x7E) >> 1;
                if (nalType >= 32 && nalType <= 35) { hevcVps = true; break; }
            }
        }
        const match = (nal4 > 0 || hevcVps) ? ' *** MATCH!' : '';
        console.log(`  ${label} (${key.length}B): nal4=${nal4} nal3=${nal3} hevcVPS=${hevcVps}${match} first16=${dec.slice(0,16).toString('hex')}`);
        if (nal4 > 0 || hevcVps) {
            console.log(`    KEY FOUND! key=${key.toString('hex')}`);
            console.log(`    first 64: ${dec.slice(0,64).toString('hex')}`);
            return true;
        }
    } catch (e) {
        console.log(`  ${label}: error: ${e.message}`);
    }
    return false;
}

function countOcc(buf, pat) {
    let c = 0, i = 0;
    while ((i = buf.indexOf(pat, i)) !== -1) { c++; i += pat.length; }
    return c;
}

// Load JS
const context = {
    console: { log(){}, error(){}, warn(){}, debug(){}, info(){} },
    navigator: { userAgent: 'Mozilla/5.0', platform: 'Win32', language: 'zh-CN', canPlayType: () => '' },
    document: { createElement: () => ({setAttribute(){},appendChild(){},style:{},getContext:()=>null,addEventListener(){}}), getElementsByTagName: () => [{appendChild(){},addEventListener(){}}], getElementById: () => null, body: {appendChild(){},addEventListener(){}}, head: {appendChild(){}}, addEventListener(){}, removeEventListener(){}, cookie:'', referrer:'', title:'', URL:'https://www.youku.com/', domain:'youku.com', documentElement:{style:{}} },
    location: { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:', pathname: '/', search: '', hash: '', origin: 'https://www.youku.com' },
    localStorage: { getItem: () => null, setItem(){}, removeItem(){} },
    sessionStorage: { getItem: () => null, setItem(){}, removeItem(){} },
    performance: { now: () => Date.now(), timing: { navigationStart: 0 }, getEntries: () => [] },
    screen: { width: 1920, height: 1080 },
    history: { pushState(){}, replaceState(){}, back(){}, forward(){}, go(){} },
    setTimeout: (fn) => { try { fn(); } catch(e) {} return 0; }, clearTimeout(){}, setInterval: () => 0, clearInterval(){},
    btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
    atob: (s) => Buffer.from(s, 'base64').toString('binary'),
    escape, unescape, decodeURIComponent, encodeURIComponent, encodeURI, decodeURI,
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
context.window = context; context.self = context; context.global = context; context.globalThis = context;
vm.createContext(context);

let jsCode = fs.readFileSync(JS_FILE, 'utf-8').replace('decodeURIComponent(escape(f.stringify(r)))', 'f.stringify(r)');
vm.runInContext(jsCode, context, { timeout: 30000 });
console.log('JS loaded\n');

// Get _sce_lgtcaygl result (24 bytes!)
const lgtc = context._sce_lgtcaygl(R1_RANDOM);
console.log(`_sce_lgtcaygl(R1): ${lgtc}`);
const lgtcDecoded = Buffer.from(lgtc, 'base64');
console.log(`  decoded: ${lgtcDecoded.toString('hex')} (${lgtcDecoded.length}B)`);

// Test all key candidates
console.log('\n=== Testing key candidates ===');

// 1. _sce_lgtcaygl result as AES-192 key
testKey(lgtcDecoded, 'lgtcaygl_24B');
testKey(lgtcDecoded, 'lgtcaygl_24B_full', fullPes);

// 2. copyrightDRM with fixed r="xWrtQpP4Z4RsrRCY"
const r1 = "xWrtQpP4Z4RsrRCY";
let d1 = crypto.createDecipheriv('aes-128-ecb', Buffer.from(r1, 'ascii'), null);
d1.setAutoPadding(false);
const key2 = Buffer.concat([d1.update(Buffer.from(ENCRYPTR_SERVER, 'base64')), d1.final()]);
let d2 = crypto.createDecipheriv('aes-128-ecb', key2, null);
d2.setAutoPadding(false);
const raw = Buffer.concat([d2.update(Buffer.from(COPYRIGHT_KEY, 'base64')), d2.final()]);
console.log(`\ncopyrightDRM(r=xWrtQpP4Z4RsrRCY):`);
console.log(`  key_2: ${key2.toString('hex')}`);
console.log(`  raw: ${raw.toString('hex')} (${raw.length}B)`);
testKey(key2, 'key_2_web_r');
testKey(raw.slice(0,16), 'raw[:16]_web_r');
testKey(raw.slice(16,32), 'raw[16:32]_web_r');

// 3. Try _sce_lgtcaygl as the r value in copyrightDRM
let d3 = crypto.createDecipheriv('aes-128-ecb', lgtcDecoded.slice(0,16), null);
d3.setAutoPadding(false);
const key2_lgtc = Buffer.concat([d3.update(Buffer.from(ENCRYPTR_SERVER, 'base64')), d3.final()]);
let d4 = crypto.createDecipheriv('aes-128-ecb', key2_lgtc, null);
d4.setAutoPadding(false);
const raw_lgtc = Buffer.concat([d4.update(Buffer.from(COPYRIGHT_KEY, 'base64')), d4.final()]);
console.log(`\ncopyrightDRM(r=lgtcaygl[:16]):`);
console.log(`  key_2: ${key2_lgtc.toString('hex')}`);
console.log(`  raw: ${raw_lgtc.toString('hex')} (${raw_lgtc.toString('hex').length/2}B)`);
testKey(key2_lgtc, 'key_2_lgtc_r');
testKey(raw_lgtc.slice(0,16), 'raw[:16]_lgtc_r');

// 4. Try _sce_lgtcaygl result directly as copyright_key
// Maybe lgtcaygl is the intermediate that's then used as the AES key for copyright_key decryption
let d5 = crypto.createDecipheriv('aes-192-ecb', lgtcDecoded, null);
d5.setAutoPadding(false);
try {
    const dec_ck = Buffer.concat([d5.update(Buffer.from(COPYRIGHT_KEY, 'base64')), d5.final()]);
    console.log(`\nlgtcaygl decrypt copyright_key:`);
    console.log(`  result: ${dec_ck.toString('hex')} (${dec_ck.length}B)`);
    testKey(dec_ck.slice(0,16), 'lgtc_dec_ck[:16]');
    testKey(dec_ck.slice(16,32), 'lgtc_dec_ck[16:32]');
} catch(e) { console.log(`  lgtc decrypt copyright_key failed: ${e.message}`); }

// 5. Try lgtcaygl as the key for encryptR_server
let d6 = crypto.createDecipheriv('aes-192-ecb', lgtcDecoded, null);
d6.setAutoPadding(false);
try {
    const dec_ers = Buffer.concat([d6.update(Buffer.from(ENCRYPTR_SERVER, 'base64')), d6.final()]);
    console.log(`\nlgtcaygl decrypt encryptR_server:`);
    console.log(`  result: ${dec_ers.toString('hex')} (${dec_ers.length}B)`);
    // Then use that to decrypt copyright_key
    let d7 = crypto.createDecipheriv('aes-128-ecb', dec_ers, null);
    d7.setAutoPadding(false);
    const dec_ck2 = Buffer.concat([d7.update(Buffer.from(COPYRIGHT_KEY, 'base64')), d7.final()]);
    console.log(`  then decrypt copyright_key: ${dec_ck2.toString('hex')} (${dec_ck2.length}B)`);
    testKey(dec_ck2.slice(0,16), 'lgtc->ers->ck[:16]');
    testKey(dec_ck2.slice(16,32), 'lgtc->ers->ck[16:32]');
} catch(e) { console.log(`  failed: ${e.message}`); }

// 6. Try: maybe R1Random base64-decoded is the r (16 bytes)
const r1raw = Buffer.from(R1_RANDOM, 'base64');
console.log(`\nR1Random decoded: ${r1raw.toString('hex')} (${r1raw.length}B)`);
let d8 = crypto.createDecipheriv('aes-128-ecb', r1raw, null);
d8.setAutoPadding(false);
const key2_r1raw = Buffer.concat([d8.update(Buffer.from(ENCRYPTR_SERVER, 'base64')), d8.final()]);
let d9 = crypto.createDecipheriv('aes-128-ecb', key2_r1raw, null);
d9.setAutoPadding(false);
const raw_r1raw = Buffer.concat([d9.update(Buffer.from(COPYRIGHT_KEY, 'base64')), d9.final()]);
console.log(`copyrightDRM(r=R1Random_decoded):`);
console.log(`  key_2: ${key2_r1raw.toString('hex')}`);
console.log(`  raw: ${raw_r1raw.toString('hex')} (${raw_r1raw.length}B)`);
testKey(key2_r1raw, 'key_2_r1raw');
testKey(raw_r1raw.slice(0,16), 'raw[:16]_r1raw');
testKey(raw_r1raw.slice(16,32), 'raw[16:32]_r1raw');

// 7. The 18-byte _sce_dlgtqred result - try various windows
const dlgt = [0, 64, 0, 3, 32, 0, 108, 0, 18, 0, 128, 0, 104, 11, 128, 0, 0, 0];
console.log(`\n_dlgtqred 18 bytes: ${dlgt.map(b=>b.toString(16).padStart(2,'0')).join('')}`);
// Maybe every other byte? (take bytes at even indices)
const evenBytes = Buffer.from(dlgt.filter((_, i) => i % 2 === 0));
const oddBytes = Buffer.from(dlgt.filter((_, i) => i % 2 === 1));
console.log(`  even bytes: ${evenBytes.toString('hex')} (${evenBytes.length}B)`);
console.log(`  odd bytes: ${oddBytes.toString('hex')} (${oddBytes.length}B)`);
testKey(evenBytes, 'dlgt_even');
testKey(oddBytes, 'dlgt_odd');
