// Run _sce_dlgtqred by loading the obfuscated JS in Node.js global scope
// The JS uses eval() to define functions globally, so we need to run it directly

const fs = require('fs');
const crypto = require('crypto');

const R1_RANDOM = "EmlTWqfjgNExE6ongWjf6w==";
const ENCRYPTR_SERVER = "rIsBBcYjaN88Fnj00PlLGQ==";
const COPYRIGHT_KEY = "0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=";

const JS_FILE = "C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches\\static\\904ddb4d0e70418993e1854359d9b066.js";

// Set up globals that the JS expects
global.navigator = { 
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 
    platform: 'Win32', 
    language: 'zh-CN',
    canPlayType: () => '',
    appName: 'Netscape',
    appVersion: '5.0',
};
global.document = { 
    createElement: () => ({setAttribute(){},appendChild(){},style:{},getContext:()=>null,addEventListener(){}}), 
    getElementsByTagName: () => [{appendChild(){},addEventListener(){}}], 
    getElementById: () => null, 
    body: {appendChild(){},addEventListener(){}}, 
    head: {appendChild(){}}, 
    addEventListener(){}, removeEventListener(){}, 
    cookie:'', referrer:'', title:'', URL:'https://www.youku.com/', 
    domain:'youku.com', documentElement:{style:{}} 
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
global.localStorage = { getItem: () => null, setItem(){}, removeItem(){} };
global.sessionStorage = { getItem: () => null, setItem(){}, removeItem(){} };
global.screen = { width: 1920, height: 1080 };
global.performance = { now: () => Date.now(), timing: { navigationStart: 0 } };
global.btoa = (s) => Buffer.from(s, 'binary').toString('base64');
global.atob = (s) => Buffer.from(s, 'base64').toString('binary');

// Load JS code
let jsCode = fs.readFileSync(JS_FILE, 'utf-8');
console.log(`JS file: ${jsCode.length} chars`);

// Patch the escape/decodeURIComponent issue
// The original code uses: decodeURIComponent(escape(str)) for UTF-8 conversion
// In Node.js, this should work, but let's patch it just in case
const originalCode = jsCode;
jsCode = jsCode.replace(/decodeURIComponent\(escape\(([^)]+)\)\)/g, '$1');

console.log('Patched. Running JS in global scope...');

try {
    // Use indirect eval to run in global scope
    const evalResult = (0, eval)(jsCode);
    console.log('JS executed. evalResult:', typeof evalResult);
} catch(e) {
    console.log('JS execution error:', e.message);
    console.log('Stack:', e.stack?.substring(0, 500));
}

// Check if functions are now defined globally
console.log('\n=== Checking global functions ===');
console.log('_sce_r_skjhfnck:', typeof _sce_r_skjhfnck);
console.log('_sce_lgtcaygl:', typeof _sce_lgtcaygl);
console.log('_sce_dlgtqred:', typeof _sce_dlgtqred);
console.log('_Cc_S_drskf_usiunsn_:', typeof _Cc_S_drskf_usiunsn_);

// If the module is available via _Cc_S_drskf_usiunsn_
if (typeof _Cc_S_drskf_usiunsn_ !== 'undefined') {
    console.log('\n=== _Cc_S_drskf_usiunsn_ keys ===');
    console.log(Object.keys(_Cc_S_drskf_usiunsn_));
}

// Try calling _sce_dlgtqred
if (typeof _sce_dlgtqred === 'function') {
    console.log('\n=== Calling _sce_dlgtqred(R1Random, encryptRServer, copyrightKey) ===');
    try {
        const result = _sce_dlgtqred(R1_RANDOM, ENCRYPTR_SERVER, COPYRIGHT_KEY);
        console.log(`Result type: ${typeof result}`);
        console.log(`Result: ${JSON.stringify(result)}`);
        
        if (typeof result === 'string') {
            console.log(`String value: "${result}"`);
            console.log(`Length: ${result.length}`);
            // Try base64 decode
            try {
                const dec = Buffer.from(result, 'base64');
                console.log(`Base64 decoded: ${dec.toString('hex')} (${dec.length}B)`);
            } catch(e) {}
            // Try as ASCII
            console.log(`ASCII bytes: ${Buffer.from(result, 'ascii').toString('hex')}`);
        } else if (result && result.length !== undefined) {
            console.log(`Array-like, length: ${result.length}`);
            const arr = Array.from(result);
            console.log(`Values: [${arr.join(', ')}]`);
            console.log(`Hex: ${arr.map(b => (b & 0xFF).toString(16).padStart(2, '0')).join('')}`);
        }
    } catch(e) {
        console.log(`Error: ${e.message}`);
        console.log(`Stack: ${e.stack?.substring(0, 500)}`);
    }
} else {
    console.log('\n_sce_dlgtqred not found. Trying alternative approaches...');
    
    // Maybe the functions are defined on a different object
    // Check if there's a global object with the functions
    for (const key of Object.keys(global)) {
        if (key.includes('sce') || key.includes('drm') || key.includes('Cc_S')) {
            console.log(`  Found global: ${key} = ${typeof global[key]}`);
        }
    }
}
