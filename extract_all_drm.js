// Extract ALL DRM fields from the YKV dbInfo
const fs = require('fs');
const path = require('path');

const YKV = String.raw`D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv`;
const YK_HEADER = 34;

const fd = fs.openSync(YKV, 'r');
const fsize = fs.statSync(YKV).size;

// Read trailer
const trailer = Buffer.alloc(16);
fs.readSync(fd, trailer, 0, 16, fsize - 16);
const trStr = trailer.toString('utf8');
const lt = trStr.split('\0')[0].trim();
const ml = parseInt(lt, 10);

// Read manifest
const manifestBuf = Buffer.alloc(ml);
fs.readSync(fd, manifestBuf, 0, ml, fsize - 16 - ml);
const decoded = decodeURIComponent(manifestBuf.toString('utf8'));
const manifest = JSON.parse(decoded);

// Find dbInfo
let dbInfoEntry = null;
for (const e of manifest) {
  if (e && typeof e === 'object' && e.name === 'dbInfo') {
    dbInfoEntry = e;
    break;
  }
}

if (!dbInfoEntry) {
  console.log('No dbInfo found');
  process.exit(1);
}

const info = dbInfoEntry.info;
const configInfo = info.configInfo;

// 1. R1Random from configInfo
console.log('=== R1Random ===');
console.log('configInfo.R1Random:', configInfo.R1Random);
console.log('Decoded length:', Buffer.from(configInfo.R1Random, 'base64').length);
console.log('Decoded hex:', Buffer.from(configInfo.R1Random, 'base64').toString('hex'));

// 2. Full stream data
console.log('\n=== Full stream data ===');
const streams = configInfo.ups.data.data.stream;
for (let i = 0; i < streams.length; i++) {
  const s = streams[i];
  console.log(`\n--- Stream ${i} ---`);
  console.log('Keys:', Object.keys(s).join(', '));
  // Print all non-segs fields
  for (const k of Object.keys(s)) {
    if (k === 'segs') {
      console.log(`  segs: [${s.segs.length} items]`);
    } else {
      const v = s[k];
      if (typeof v === 'object') {
        console.log(`  ${k}:`, JSON.stringify(v));
      } else {
        console.log(`  ${k}: ${v}`);
      }
    }
  }
}

// 3. Search for copyright_key anywhere in the data
console.log('\n=== Searching for copyright_key ===');
function deepSearch(obj, target, path = '') {
  if (obj === null || obj === undefined) return;
  if (typeof obj === 'string') {
    if (obj.includes(target) || obj.toLowerCase().includes(target.toLowerCase())) {
      console.log(`  Found at ${path}: ${obj.slice(0, 200)}`);
    }
    return;
  }
  if (typeof obj === 'object') {
    for (const k of Object.keys(obj)) {
      if (k.toLowerCase().includes(target.toLowerCase())) {
        console.log(`  Key "${k}" at ${path}: ${JSON.stringify(obj[k]).slice(0, 300)}`);
      }
      deepSearch(obj[k], target, `${path}.${k}`);
    }
  }
}
deepSearch(configInfo, 'copyright_key');
deepSearch(configInfo, 'copyright');
deepSearch(configInfo, 'stream_ext');

// 4. Search for encryptR in configInfo
console.log('\n=== Searching for encryptR ===');
deepSearch(configInfo, 'encryptR');

// 5. Check video field for drm_type
console.log('\n=== video.drm_type ===');
const video = configInfo.ups.data.data.video;
console.log('video.drm_type:', video.drm_type);
console.log('video keys:', Object.keys(video).join(', '));

// 6. Dump first stream fully
console.log('\n=== First stream full JSON (truncated) ===');
console.log(JSON.stringify(streams[0]).slice(0, 2000));

fs.closeSync(fd);
