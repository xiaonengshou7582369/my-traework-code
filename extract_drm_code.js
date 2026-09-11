// Extract DRM-related code from Youku JS files
const fs = require('fs');
const path = require('path');

const jsDir = 'C:\\Users\\Administrator\\AppData\\Roaming\\youku-app\\local_caches';
const files = [
    path.join(jsDir, 'webPlayerVersion', '2.2.0', 'c9625326d7565e79dd24365cad6053e5.js'),
    path.join(jsDir, 'webPlayerVersion', '2.2.0', '407bd122d0617027020872cd68e623fc.js'),
    path.join(jsDir, 'static', '904ddb4d0e70418993e1854359d9b066.js'),
    path.join(jsDir, 'static', '06d208ad6fdedaaf1868f7dc6ad0a0bf.js'),
];

const searchTerms = ['_sce_r_skjhfnck', '_sce_lgtcaygl', '_sce_dlgtqred', 'copyrightDRM', 'encryptR', 'copyright_key', 'R1Random'];

for (const file of files) {
    try {
        const code = fs.readFileSync(file, 'utf-8');
        const basename = path.basename(file);
        console.log(`\n=== ${basename} (${code.length} chars) ===`);
        
        for (const term of searchTerms) {
            const idx = code.indexOf(term);
            if (idx >= 0) {
                // Get surrounding context (200 chars before and after)
                const start = Math.max(0, idx - 200);
                const end = Math.min(code.length, idx + term.length + 200);
                const context = code.substring(start, end);
                console.log(`\n--- "${term}" at offset ${idx} ---`);
                console.log(context);
            }
        }
    } catch(e) {
        console.log(`Error reading ${file}: ${e.message}`);
    }
}

// Also check all static JS files
const staticDir = path.join(jsDir, 'static');
if (fs.existsSync(staticDir)) {
    const allJs = fs.readdirSync(staticDir).filter(f => f.endsWith('.js'));
    for (const f of allJs) {
        const fp = path.join(staticDir, f);
        try {
            const code = fs.readFileSync(fp, 'utf-8');
            for (const term of ['_sce_r_skjhfnck', 'copyrightDRM']) {
                if (code.includes(term)) {
                    const idx = code.indexOf(term);
                    const start = Math.max(0, idx - 300);
                    const end = Math.min(code.length, idx + term.length + 300);
                    console.log(`\n=== ${f}: "${term}" at ${idx} ===`);
                    console.log(code.substring(start, end));
                }
            }
        } catch(e) {}
    }
}

// Check v2/static
const v2StaticDir = path.join(jsDir, 'v2', 'static');
if (fs.existsSync(v2StaticDir)) {
    const allJs = fs.readdirSync(v2StaticDir).filter(f => f.endsWith('.js'));
    for (const f of allJs) {
        const fp = path.join(v2StaticDir, f);
        try {
            const code = fs.readFileSync(fp, 'utf-8');
            for (const term of ['_sce_r_skjhfnck', 'copyrightDRM']) {
                if (code.includes(term)) {
                    const idx = code.indexOf(term);
                    const start = Math.max(0, idx - 300);
                    const end = Math.min(code.length, idx + term.length + 300);
                    console.log(`\n=== v2/${f}: "${term}" at ${idx} ===`);
                    console.log(code.substring(start, end));
                }
            }
        } catch(e) {}
    }
}
