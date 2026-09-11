"""Deeper analysis of extracted TS to determine if it's actually encrypted."""
import os
import sys
import json
from pathlib import Path
from urllib.parse import unquote

YK_HEADER_SIZE = 34


def read_manifest(ykv_path: Path):
    fs = ykv_path.stat().st_size
    with ykv_path.open("rb") as f:
        f.seek(-16, os.SEEK_END)
        tr = f.read(16).decode("utf-8", "replace")
    lt = tr.split("\x00", 1)[0].strip()
    ml = int(lt)
    with ykv_path.open("rb") as f:
        f.seek(-(16 + ml), os.SEEK_END)
        raw = f.read(ml)
    decoded = unquote(raw.decode("utf-8"))
    return json.loads(decoded)


def extract_ts(ykv_path: Path, seg: dict) -> bytes:
    offset = int(seg["offset"])
    size = int(seg["size"])
    payload_start = offset + YK_HEADER_SIZE
    payload_size = size - YK_HEADER_SIZE
    with ykv_path.open("rb") as f:
        f.seek(payload_start)
        return f.read(payload_size)


def main(ykv_path: Path) -> None:
    manifest = read_manifest(ykv_path)
    ts_segs = [m for m in manifest if str(m.get("name", "")).lower().endswith(".ts")]
    ts_segs.sort(key=lambda s: int(s["name"].split(".")[0]))

    data = extract_ts(ykv_path, ts_segs[0])
    print(f"1.ts size: {len(data)} bytes")

    # Count good sync bytes across ALL packets
    n_packets = len(data) // 188
    bad_sync = 0
    for i in range(n_packets):
        if data[i * 188] != 0x47:
            bad_sync += 1
    print(f"TS packets: {n_packets}, bad sync: {bad_sync}")

    # Check TSC (transport_scrambling_control) on all packets
    # TSC = bits 7-6 of byte 3
    tsc_values = {}
    for i in range(n_packets):
        byte3 = data[i * 188 + 3]
        tsc = (byte3 >> 6) & 0x3
        tsc_values[tsc] = tsc_values.get(tsc, 0) + 1
    print(f"\nTSC distribution:")
    for tsc, cnt in sorted(tsc_values.items()):
        label = {0: "not scrambled", 1: "reserved", 2: "scrambled (even key)",
                 3: "scrambled (odd key)"}.get(tsc, "?")
        print(f"  TSC={tsc} ({label}): {cnt} packets")

    # PID distribution
    from collections import Counter
    pids = Counter()
    for i in range(n_packets):
        pkt = data[i * 188: (i + 1) * 188]
        pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
        pids[pid] += 1
    print(f"\nPID distribution:")
    for pid, cnt in pids.most_common(10):
        print(f"  PID {pid:5d} (0x{pid:04X}): {cnt} packets")

    # Look at first few PES start packets
    print(f"\n--- First PES packets (PUSI=1) ---")
    seen_pids = set()
    for i in range(min(n_packets, 100)):
        pkt = data[i * 188: (i + 1) * 188]
        pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
        pusi = (pkt[1] >> 6) & 1
        if pusi == 1 and pid not in seen_pids:
            seen_pids.add(pid)
            adaptation = (pkt[3] >> 4) & 0x3
            payload_start = 4
            if adaptation in (2, 3):
                af_len = pkt[4]
                payload_start = 5 + af_len
            payload = pkt[payload_start:payload_start + 48]
            tsc = (pkt[3] >> 6) & 0x3
            print(f"  pkt[{i}] PID={pid:5d} (0x{pid:04X}) PUSI=1 AFC={adaptation} TSC={tsc}")
            print(f"          payload: {payload.hex()}")
            # Check for PES start code
            if payload[:3] == b"\x00\x00\x01":
                stream_id = payload[3]
                print(f"          -> PES stream_id=0x{stream_id:02X} "
                      f"(video=0xE0-0xEF, audio=0xC0-0xDF)")
            elif payload[0] == 0x00:
                # Could be a section (pointer_field)
                pf = payload[0]
                section = payload[1:]
                print(f"          -> pointer_field={pf}, section starts: "
                      f"table_id=0x{section[0]:02X}")

    # Check if data ends with stuffing (0xFF bytes at the end)
    last_bytes = data[-32:]
    print(f"\nLast 32 bytes: {last_bytes.hex()}")

    # Save extracted TS for ffmpeg test
    out = Path("test_1.ts")
    out.write_bytes(data)
    print(f"\nSaved extracted 1.ts to {out.absolute()} ({len(data)} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python probe_ts.py <ykv>")
        sys.exit(1)
    main(Path(sys.argv[1]))
