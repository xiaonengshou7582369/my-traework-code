// Extract and display the embedded m3u8 file from the YKV.
const fs = require('fs');
const path = require('path');

const YKV = String.raw`D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv`;
const YK_HEADER = 34;

const fd = fs.openSync(YKV, 'r');
const fsize = fs.statSync(YKV).size;

// Read trailer (last 16 bytes)
const trailer = Buffer.alloc(16);
fs.readSync(fd, trailer, 0, 16, fsize - 16);
const trStr = trailer.toString('utf8');
const lt = trStr.split('\0')[0].trim();
const ml = parseInt(lt, 10);
console.log(`Trailer: '${trStr}', manifest length: ${ml}`);

// Read manifest
const manifestBuf = Buffer.alloc(ml);
fs.readSync(fd, manifestBuf, 0, ml, fsize - 16 - ml);
const decoded = decodeURIComponent(manifestBuf.toString('utf8'));
const manifest = JSON.parse(decoded);

console.log(`Manifest entries: ${manifest.length}`);

// Find m3u8 entry
let m3u8Entry = null;
for (const e of manifest) {
  if (e && typeof e === 'object' && e.name === 'youku.m3u8') {
    m3u8Entry = e;
    break;
  }
}

if (m3u8Entry) {
  const offset = parseInt(m3u8Entry.offset) + YK_HEADER;
  const size = parseInt(m3u8Entry.size) - YK_HEADER;
  const buf = Buffer.alloc(size);
  fs.readSync(fd, buf, 0, size, offset);
  console.log('\n=== Embedded m3u8 ===');
  console.log(buf.toString('utf8'));
} else {
  console.log('No m3u8 entry found');
}

// Find dbInfo entry for DRM params
let dbInfoEntry = null;
for (const e of manifest) {
  if (e && typeof e === 'object' && e.name === 'dbInfo') {
    dbInfoEntry = e;
    break;
  }
}

if (dbInfoEntry) {
  console.log('\n=== dbInfo found ===');
  const info = dbInfoEntry.info;
  // Search for DRM-related fields
  const configInfo = info.configInfo;
  if (configInfo) {
    console.log('configInfo keys:', Object.keys(configInfo).join(', '));
    const ups = configInfo.ups;
    if (ups && ups.data && ups.data.data) {
      const d = ups.data.data;
      console.log('\n=== DRM fields in ups.data.data ===');
      for (const key of Object.keys(d)) {
        const v = d[key];
        if (typeof v === 'string' && v.length < 200) {
          console.log(`  ${key}: ${v}`);
        } else if (typeof v === 'object') {
          console.log(`  ${key}: [object with keys: ${Object.keys(v).join(',')}]`);
        }
      }
      // Look specifically for stream-related DRM
      if (d.stream) {
        console.log('\n=== streams ===');
        for (const s of d.stream) {
          console.log(`  stream: ${JSON.stringify({drm_type: s.drm_type, extag: s.extag, key_index: s.key_index, encryptR_client: s.encryptR_client, encryptR_server: s.encryptR_server})}`);
          if (s.segs) {
            console.log(`    segs count: ${s.segs.length}`);
            if (s.segs[0]) {
              console.log(`    seg[0] keys: ${Object.keys(s.segs[0]).join(', ')}`);
              console.log(`    seg[0]: ${JSON.stringify(s.segs[0]).slice(0, 500)}`);
            }
          }
        }
      }
    }
  }
}

fs.closeSync(fd);
