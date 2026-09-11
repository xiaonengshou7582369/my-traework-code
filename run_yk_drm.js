// Run Youku's actual DRM JS to derive the decryption key
// Loads the obfuscated JS and calls _sce_dlgtqred with known parameters

const fs = require('fs');
const path = require('path');

// Set up a fake browser environment
global.window = global;
global.navigator = { userAgent: 'Mozilla/5.0' };
global.document = {
    createElement: () => ({ setAttribute: () => {}, appendChild: () => {} }),
    getElementsByTagName: () => [{ appendChild: () => {} }]
};

// Path to the Youku DRM JS file
const jsFile = path.join('C:', 'Users', 'Administrator', 'AppData', 'Roaming', 'youku-app', 'local_caches', 'static', '904ddb4d0e70418993e1854359d9b066.js');

// Load and execute the JS
const jsCode = fs.readFileSync(jsFile, 'utf-8');
try {
    eval(jsCode);
} catch (e) {
    console.error('Error loading JS:', e.message);
}

// Check if the functions are available
console.log('Functions available:');
console.log('  _sce_dlgtqred:', typeof window._sce_dlgtqred);
console.log('  _sce_lgtcaygl:', typeof window._sce_lgtcaygl);
console.log('  _sce_r_skjhfnck:', typeof window._sce_r_skjhfnck);

// Known parameters from data.json for episode 1 (vid=XNTk3MzA5NzgzMg==)
const R1 = 'EmlTWqfjgNExE6ongWjf6w==';  // R1Random
const encryptRServer = 'rIsBBcYjaN88Fnj00PlLGQ==';
const copyrightKey = '0WZJpdEknsuQl4OoWRlTWSuffXj1MlrSry7rj7M+vQc=';

// Try to call _sce_dlgtqred to derive the key
if (typeof window._sce_dlgtqred === 'function') {
    try {
        const key = window._sce_dlgtqred(R1, encryptRServer, copyrightKey);
        console.log('\nDerived key:', key);
        console.log('Type:', typeof key);
        if (typeof key === 'string') {
            console.log('Length:', key.length);
            console.log('Hex:', Buffer.from(key).toString('hex'));
        } else if (Buffer.isBuffer(key) || key instanceof Uint8Array) {
            console.log('Bytes:', Buffer.from(key).toString('hex'));
        }
    } catch (e) {
        console.error('Error calling _sce_dlgtqred:', e.message);
        console.error(e.stack);
    }
} else {
    console.log('\n_sce_dlgtqred not found. Trying alternative approach...');
    // The function might be defined but not on window
    console.log('All _sce_ keys:', Object.keys(global).filter(k => k.startsWith('_sce_')));
}
