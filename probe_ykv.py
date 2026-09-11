"""Analyze encryption pattern in a YKV-extracted .ts file."""
import sys
from pathlib import Path
from collections import Counter

def analyze(path: Path) -> None:
    data = path.read_bytes()
    print(f"File: {path.name}")
    print(f"Size: {len(data)} bytes ({len(data) / 188} TS packets)")

    # Count HEVC/H.264 NAL start codes (00 00 00 01 or 00 00 01)
    nal4 = data.count(b"\x00\x00\x00\x01")
    nal3 = data.count(b"\x00\x00\x01")
    print(f"\nNAL start code 00 00 00 01 count: {nal4}")
    print(f"NAL start code 00 00 01 count: {nal3} (includes 4-byte ones)")

    # Find positions of NAL start codes
    positions4 = []
    pos = 0
    while True:
        idx = data.find(b"\x00\x00\x00\x01", pos)
        if idx == -1:
            break
        positions4.append(idx)
        pos = idx + 4
    print(f"\nFirst 10 NAL 00 00 00 01 positions: {positions4[:10]}")
    print(f"Last 5 NAL 00 00 00 01 positions: {positions4[-5:]}")

    # Per-TS-packet analysis: is the 4-byte header intact (0x47)?
    bad_sync = 0
    for i in range(len(data) // 188):
        if data[i * 188] != 0x47:
            bad_sync += 1
    print(f"\nTS packets with bad sync byte: {bad_sync}/{len(data) // 188}")

    # Per-TS-packet PID distribution
    pids = Counter()
    for i in range(len(data) // 188):
        pkt = data[i * 188: (i + 1) * 188]
        if pkt[0] == 0x47:
            pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
            pids[pid] += 1
    print(f"\nPID distribution (top 10):")
    for pid, cnt in pids.most_common(10):
        print(f"  PID {pid:5d} (0x{pid:04X}): {cnt} packets")

    # Look at payload of first video PES packet
    # Standard: video PID often 0x100 (256), 0x101 (257), 0x102 (258), etc.
    # Find a PUSI=1 packet on a likely video PID
    print(f"\n--- First PES start packets (PUSI=1) by PID ---")
    seen_pids = set()
    for i in range(min(len(data) // 188, 200)):
        pkt = data[i * 188: (i + 1) * 188]
        if pkt[0] != 0x47:
            continue
        pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
        pusi = (pkt[1] >> 6) & 1
        if pusi == 1 and pid not in seen_pids:
            seen_pids.add(pid)
            # Show payload after the 4-byte TS header (and possible adaptation field)
            adaptation = (pkt[3] >> 4) & 0x3
            payload_start = 4
            if adaptation in (2, 3):
                af_len = pkt[4]
                payload_start = 5 + af_len
            payload = pkt[payload_start:payload_start + 32]
            print(f"  pkt[{i}] PID={pid:5d} PUSI=1 adaptation={adaptation}")
            print(f"          payload (32 bytes): {payload.hex()}")
            # Look for PES start code 00 00 01
            if payload[:3] == b"\x00\x00\x01":
                stream_id = payload[3]
                print(f"          -> PES stream_id=0x{stream_id:02X}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python probe_ykv.py <ts_file>")
        sys.exit(1)
    analyze(Path(sys.argv[1]))
