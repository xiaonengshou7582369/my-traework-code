"""Analyze first TS segment of a ykv to understand encryption scope."""
import os
import json
import sys
from pathlib import Path
from urllib.parse import unquote

YK_HEADER_SIZE = 34
TS_PACKET_SIZE = 188


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
    return json.loads(unquote(raw.decode("utf-8")))


def main(ykv_path: Path) -> None:
    manifest = read_manifest(ykv_path)
    ts = [m for m in manifest if str(m.get("name", "")).lower().endswith(".ts")]
    ts.sort(key=lambda s: int(s["name"].split(".")[0]))

    seg = ts[0]
    print(f"First seg: {seg['name']} offset={seg['offset']} size={seg['size']}")

    # Read first 256 bytes at the segment offset (includes YK header)
    with ykv_path.open("rb") as f:
        f.seek(int(seg["offset"]))
        head = f.read(256)
    print(f"\n--- At segment offset (includes YK header) ---")
    print(f"First 64B: {head[:64].hex()}")
    print(f"YK header (34B): {head[:34].hex()}")
    print(f"Byte at +34: 0x{head[34]:02x} (is 0x47 sync? {head[34] == 0x47})")

    # Extract the full segment (after YK header) and analyze
    payload_start_offset = int(seg["offset"]) + YK_HEADER_SIZE
    payload_size = int(seg["size"]) - YK_HEADER_SIZE
    with ykv_path.open("rb") as f:
        f.seek(payload_start_offset)
        data = f.read(payload_size)

    n_packets = len(data) // TS_PACKET_SIZE
    print(f"\nSegment payload: {len(data)} bytes = {n_packets} TS packets")

    # Count NAL start codes in the WHOLE segment
    nal4 = data.count(b"\x00\x00\x00\x01")
    nal3 = data.count(b"\x00\x00\x01")
    print(f"NAL 00 00 00 01 count: {nal4}")
    print(f"NAL 00 00 01 count: {nal3}")

    # Find positions of first few NAL start codes
    positions = []
    pos = 0
    while True:
        idx = data.find(b"\x00\x00\x00\x01", pos)
        if idx == -1:
            break
        positions.append(idx)
        pos = idx + 4
    print(f"First 10 NAL 4-byte positions: {positions[:10]}")
    if positions:
        print(f"  NAL at first pos ({positions[0]}): "
              f"data[{positions[0]}:{positions[0]+8}] = {data[positions[0]:positions[0]+8].hex()}")

    # Check the first video PES packet (PID 0x100 = 256) with PUSI=1
    print(f"\n--- First video PES packet (PID=256, PUSI=1) ---")
    for i in range(n_packets):
        pkt = data[i * TS_PACKET_SIZE: (i + 1) * TS_PACKET_SIZE]
        if pkt[0] != 0x47:
            continue
        pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
        pusi = (pkt[1] >> 6) & 1
        if pid == 0x0100 and pusi == 1:
            afc = (pkt[3] >> 4) & 0x3
            if afc in (2, 3):
                af_len = pkt[4]
                p_start = 5 + af_len
            else:
                p_start = 4
            pes = pkt[p_start:]
            print(f"  packet index: {i}")
            print(f"  afc={afc} payload_start={p_start}")
            print(f"  PES first 32B: {pes[:32].hex()}")
            if pes[:3] == b"\x00\x00\x01":
                stream_id = pes[3]
                pes_len = (pes[4] << 8) | pes[5]
                hdr_data_len = pes[8]
                payload_off = 9 + hdr_data_len
                print(f"  stream_id=0x{stream_id:02x} pes_len={pes_len} "
                      f"hdr_data_len={hdr_data_len}")
                print(f"  PES header data: {pes[9:9+hdr_data_len].hex()}")
                print(f"  PES payload first 32B: {pes[payload_off:payload_off+32].hex()}")
            break

    # Look at the TS packet that contains the first NAL start code
    if positions:
        nal_pos = positions[0]
        pkt_idx = nal_pos // TS_PACKET_SIZE
        pkt_offset = nal_pos % TS_PACKET_SIZE
        print(f"\n--- TS packet containing first NAL ---")
        print(f"  NAL pos={nal_pos} -> packet {pkt_idx}, offset {pkt_offset}")
        pkt = data[pkt_idx * TS_PACKET_SIZE: (pkt_idx + 1) * TS_PACKET_SIZE]
        print(f"  Packet header: {pkt[:4].hex()}")
        print(f"  Bytes around NAL: {pkt[max(0,pkt_offset-4):pkt_offset+12].hex()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python analyze_seg.py <ykv>")
        sys.exit(1)
    main(Path(sys.argv[1]))
