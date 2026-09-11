#!/usr/bin/env node
/* Check Transport Scrambling Control (TSC) field in MPEG-TS packets.
   TSC (2 bits) at byte 3 high nibble of each 188-byte packet:
     00 = not scrambled, 01 = reserved, 10 = even key, 11 = odd key
*/
const fs = require('fs');
const path = require('path');

const TS_PKT = 188;
const file = process.argv[2] || path.join(__dirname, 'probe_out', 'seg1_no_header.ts');
const data = fs.readFileSync(file);
const n = Math.min(20000, Math.floor(data.length / TS_PKT));

console.log(`File: ${file}`);
console.log(`Size: ${data.length} bytes, ${Math.floor(data.length/TS_PKT)} packets, scanning first ${n}\n`);

const pidCount = {};
const pidTsc = {};
const pidPusi = {};

for (let i = 0; i < n; i++) {
  const off = i * TS_PKT;
  if (data[off] !== 0x47) {
    console.log(`  ! sync byte mismatch at pkt ${i} (off ${off}): 0x${data[off].toString(16)}`);
    continue;
  }
  const flags = data[off+1];
  const tsc = (data[off+3] >> 6) & 0x3;
  const pusi = (flags >> 6) & 0x1;
  const pid = ((flags & 0x1F) << 8) | data[off+2];
  pidCount[pid] = (pidCount[pid]||0) + 1;
  if (!pidTsc[pid]) pidTsc[pid] = [0,0,0,0];
  pidTsc[pid][tsc]++;
  pidPusi[pid] = (pidPusi[pid]||0) + pusi;
}

console.log('   PID   count  TSC=00  TSC=01  TSC=10  TSC=11   PUSI');
const pids = Object.keys(pidCount).map(Number).sort((a,b)=>a-b);
for (const pid of pids) {
  const c = pidTsc[pid];
  console.log(`${String(pid).padStart(6)} ${String(pidCount[pid]).padStart(7)} ` +
    `${String(c[0]).padStart(7)} ${String(c[1]).padStart(7)} ${String(c[2]).padStart(7)} ${String(c[3]).padStart(7)} ` +
    `${String(pidPusi[pid]).padStart(6)}`);
}

// PUSI packets payload inspection
console.log('\n=== First payload bytes of PUSI packets (top PIDs) ===');
const interesting = pids.filter(p => pidCount[p] > 50).slice(0, 6);
for (const pid of interesting) {
  console.log(`\nPID ${pid} (count=${pidCount[pid]}):`);
  let shown = 0;
  for (let i = 0; i < n && shown < 3; i++) {
    const off = i * TS_PKT;
    if (data[off] !== 0x47) continue;
    const flags = data[off+1];
    const pusi = (flags >> 6) & 0x1;
    const thisPid = ((flags & 0x1F) << 8) | data[off+2];
    if (thisPid !== pid || !pusi) continue;
    const tsc = (data[off+3] >> 6) & 0x3;
    const afCtrl = (data[off+3] >> 4) & 0x3;
    let payloadOff = off + 4;
    if (afCtrl & 0x2) {
      const afLen = data[off+4];
      payloadOff = off + 5 + afLen;
    }
    if ((afCtrl & 0x1) === 0) {
      console.log(`  pkt ${i}: PUSI but no payload (af_ctrl=${afCtrl})`);
      continue;
    }
    const payload = data.slice(payloadOff, payloadOff + 32);
    const hex = Buffer.from(payload).toString('hex');
    console.log(`  pkt ${i}: TSC=${tsc} af=${afCtrl} payload[0:32]=${hex}`);
    shown++;
  }
}
