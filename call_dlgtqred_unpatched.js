// Try _sce_dlgtqred without patching, and inspect the library
const fs = require('fs');
const crypto = require('crypto');

const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";

const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";

// Set up globals
global.navigator = { userAgent: 'Mozilla/5.0', platform: 'Win32', language: 'zh-CN', canPlayType: () => '' };
global.document = { createElement: () => ({setAttribute(){},appendChild(){},style:{},getContext:()=>null,addEventListener(){}}), getElementsByTagName: () => [{appendChild(){},addEventListener(){}}], getElementById: () => null, body: {appendChild(){},addEventListener(){}}, head: {appendChild(){}}, addEventListener(){}, removeEventListener(){}, cookie:'', referrer:'', title:'', URL:'https://www.youku.com/', domain:'youku.com', documentElement:{style:{}} };
global.location = { href: 'https://www.youku.com/', hostname: 'www.youku.com', protocol: 'https:', pathname: '/', search: '', hash: '', origin: 'https://www.youku.com' };
global.localStorage = { getItem: () => null, setItem(){}, removeItem(){} };
global.sessionStorage = { getItem: () => null, setItem(){}, removeItem(){} };
global.screen = { width: 1920, height: 1080 };
global.performance = { now: () => Date.now(), timing: { navigationStart: 0 } };
global.btoa = (s) => Buffer.from(s, 'binary').toString('base64');
global.atob = (s) => Buffer.from(s, 'base64').toString('binary');

// Load JS WITHOUT patching
let jsCode = fs.readFileSync(JS_FILE, 'utf-8');
console.log(`JS file: ${jsCode.length} chars (UNPATCHED)`);

try {
    (0, eval)(jsCode);
    console.log('JS executed successfully');
} catch(e) {
    console.log('JS execution error:', e.message);
}

// Check functions
console.log('\n=== Functions ===');
console.log('_sce_dlgtqred:', typeof _sce_dlgtqred);
console.log('_Cc_S_drskf_usiunsn_:', typeof _Cc_S_drskf_usiunsn_);

// Inspect the library
if (typeof _Cc_S_drskf_usiunsn_ !== 'undefined') {
    console.log('\n=== _Cc_S_drskf_usiunsn_ structure ===');
    for (const key of Object.keys(_Cc_S_drskf_usiunsn_)) {
        const val = _Cc_S_drskf_usiunsn_[key];
        console.log(`  ${key}: ${typeof val}`);
        if (typeof val === 'object' && val !== null) {
            console.log(`    keys: ${Object.keys(val).join(', ').substring(0, 200)}`);
        }
    }
    
    // Check for AES-related functions
    if (_Cc_S_drskf_usiunsn_.algo) {
        console.log('\n=== Algorithms ===');
        console.log(`Keys: ${Object.keys(_Cc_S_drskf_usiunsn_.algo).join(', ')}`);
    }
    if (_Cc_S_drskf_usiunsn_.enc) {
        console.log('\n=== Encoders ===');
        console.log(`Keys: ${Object.keys(_Cc_S_drskf_usiunsn_.enc).join(', ')}`);
    }
}

// Call _sce_dlgtqred without patch
if (typeof _sce_dlgtqred === 'function') {
    console.log('\n=== Calling _sce_dlgtqred (UNPATCHED) ===');
    try {
        const result = _sce_dlgtqred(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY);
        console.log(`Type: ${typeof result}`);
        if (result && result.length !== undefined) {
            console.log(`Length: ${result.length}`);
            const arr = Array.from(result);
            console.log(`Values: [${arr.join(', ')}]`);
            console.log(`Hex: ${arr.map(b => (b & 0xFF).toString(16).padStart(2, '0')).join('')}`);
            
            // Try to interpret as UTF-16 string
            if (result.length % 2 === 0) {
                let str16 = '';
                for (let i = 0; i < result.length; i += 2) {
                    str16 += String.fromCharCode((result[i] << 8) | result[i+1]);
                }
                console.log(`UTF-16BE: "${str16}"`);
                
                let str16le = '';
                for (let i = 0; i < result.length; i += 2) {
                    str16le += String.fromCharCode((result[i+1] << 8) | result[i]);
                }
                console.log(`UTF-16LE: "${str16le}"`);
            }
        } else if (typeof result === 'string') {
            console.log(`String: "${result}"`);
        } else if (result && typeof result === 'object') {
            console.log(`Object: ${JSON.stringify(result).substring(0, 500)}`);
            // Check if it's a CryptoJS WordArray
            if (result.words && result.sigBytes !== undefined) {
                console.log(`CryptoJS WordArray! sigBytes=${result.sigBytes}`);
                const words = result.words;
                const bytes = [];
                for (let i = 0; i < result.sigBytes; i++) {
                    bytes.push((words[i >>> 2] >>> (24 - (i % 4) * 8)) & 0xff);
                }
                console.log(`Key bytes: ${bytes.map(b => b.toString(16).padStart(2, '0')).join('')}`);
                console.log(`Key length: ${bytes.length}B`);
            }
        }
    } catch(e) {
        console.log(`Error: ${e.message}`);
        console.log(`Stack: ${e.stack?.substring(0, 800)}`);
    }
}

// Try calling with different argument combinations
if (typeof _sce_dlgtqred === 'function') {
    console.log('\n=== Trying different argument combinations ===');
    
    // Maybe R1 should be _sce_r_skjhfnck() result
    const r1_random = _sce_r_skjhfnck();
    console.log(`_sce_r_skjhfnck() = "${r1_random}"`);
    const encryptR1 = _sce_lgtcaygl(R1_RANDOM);
    console.log(`_sce_lgtcaygl(R1_RANDOM) = "${encryptR1}"`);
    
    // Try: _sce_dlgtqred(encryptR1, encryptRServer, copyrightKey)
    console.log('\n--- _sce_dlgtqred(encryptR1, encryptRServer, copyrightKey) ---');
    try {
        const result = _sce_dlgtqred(encryptR1, ENCRYPTR_SERVER, COPYRIGHT_KEY);
        console.log(`Type: ${typeof result}, Length: ${result?.length}`);
        if (result && result.length !== undefined) {
            const arr = Array.from(result);
            console.log(`Hex: ${arr.map(b => (b & 0xFF).toString(16).padStart(2, '0')).join('')}`);
        } else if (typeof result === 'string') {
            console.log(`String: "${result}"`);
        }
    } catch(e) {
        console.log(`Error: ${e.message}`);
    }
    
    // Maybe the function uses CryptoJS internally
    // Check if the result is a WordArray
    console.log('\n--- Checking if result is CryptoJS object ---');
    try {
        const result = _sce_dlgtqred(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY);
        console.log(`toString(): ${result?.toString?.()}`);
        console.log(`constructor: ${result?.constructor?.name}`);
        if (result && typeof result === 'object') {
            console.log(`All keys: ${Object.keys(result).join(', ')}`);
            for (const k of Object.keys(result)) {
                console.log(`  ${k}: ${typeof result[k]} = ${JSON.stringify(result[k])?.substring(0, 100)}`);
            }
        }
    } catch(e) {
        console.log(`Error: ${e.message}`);
    }
}
