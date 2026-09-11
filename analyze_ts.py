"""Analyze all PIDs and TSC values in TS segment."""
from pathlib import Path

data = Path(r'C:\Users\Administrator\iCloudDrive\Traework云仓库\6aa2615da516df5d0a1843ba\seg1.ts').read_bytes()
n = len(data) // 188
pids = {}
for i in range(n):
    pkt = data[i*188:(i+1)*188]
    if pkt[0] != 0x47:
        continue
    pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
    pusi = (pkt[1] >> 6) & 1
    tsc = (pkt[1] >> 3) & 0x3
    afc = (pkt[3] >> 4) & 0x3
    if pid not in pids:
        pids[pid] = {'count': 0, 'tsc': tsc, 'pusi': 0, 'afc': afc}
    pids[pid]['count'] += 1
    if pusi:
        pids[pid]['pusi'] = 1

print('Total packets:', n)
print('Unique PIDs:', len(pids))
for pid in sorted(pids.keys()):
    info = pids[pid]
    print('  PID 0x%04x: count=%4d tsc=%d pusi=%d afc=%d' % (pid, info['count'], info['tsc'], info['pusi'], info['afc']))

# For the scrambled PID (TSC=2), show first PES payload
for pid, info in pids.items():
    if info['tsc'] > 0:
        print('\n--- Scrambled PID 0x%04x (TSC=%d) ---' % (pid, info['tsc']))
        # Find first PUSI packet for this PID
        for i in range(n):
            pkt = data[i*188:(i+1)*188]
            if pkt[0] != 0x47:
                continue
            p = ((pkt[1] & 0x1F) << 8) | pkt[2]
            pu = (pkt[1] >> 6) & 1
            if p == pid and pu == 1:
                afc = (pkt[3] >> 4) & 0x3
                payload_start = 4
                if afc in (2, 3):
                    af_len = pkt[4]
                    payload_start = 5 + af_len
                pes = pkt[payload_start:]
                print('  First PUSI packet at index', i)
                print('  PES header:', pes[:9].hex())
                if pes[:3] == b'\x00\x00\x01':
                    stream_id = pes[3]
                    pes_len = (pes[4] << 8) | pes[5]
                    hdr_data_len = pes[8]
                    payload_offset = 9 + hdr_data_len
                    pes_payload = pes[payload_offset:]
                    print('  stream_id: 0x%02x' % stream_id)
                    print('  PES length:', pes_len)
                    print('  PES header data length:', hdr_data_len)
                    print('  PES payload first 32B:', pes_payload[:32].hex())
                    # Check for NAL start codes
                    nal4 = pes_payload.count(b'\x00\x00\x00\x01')
                    nal3 = pes_payload.count(b'\x00\x00\x01')
                    print('  NAL start codes (4B):', nal4, '(3B):', nal3)
                break
