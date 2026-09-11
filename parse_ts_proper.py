"""Properly parse MPEG-TS to find video/audio PIDs and check PES payloads."""
import os, json
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
YK_HEADER = 34

fs = YKV.stat().st_size
with YKV.open("rb") as f:
    f.seek(-16, os.SEEK_END)
    tr = f.read(16).decode("utf-8", "replace")
ml = int(tr.split("\x00", 1)[0].strip())
with YKV.open("rb") as f:
    f.seek(-(16 + ml), os.SEEK_END)
    raw = f.read(ml)
manifest = json.loads(unquote(raw.decode("utf-8")))

ts_segs = [m for m in manifest if isinstance(m, dict) and m.get("name", "").endswith(".ts")]
ts_segs.sort(key=lambda x: int(x["name"].replace(".ts", "")))

# Read first segment
seg = ts_segs[0]
off = int(seg["offset"]) + YK_HEADER
size = int(seg["size"]) - YK_HEADER
with YKV.open("rb") as f:
    f.seek(off)
    data = f.read(size)

def parse_ts_packets(data, max_pkts=200):
    """Parse TS packets and extract PAT, PMT, and PES info."""
    n = len(data) // 188
    pids = {}
    pat_data = None
    pmt_data = {}
    video_pids = set()
    audio_pids = set()

    for i in range(min(n, max_pkts)):
        pkt = data[i*188:(i+1)*188]
        if pkt[0] != 0x47:
            continue
        pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
        pusi = (pkt[1] >> 6) & 1
        afc = (pkt[3] >> 4) & 0x3
        cc = pkt[3] & 0x0F
        tsc = (pkt[3] >> 6) & 0x3

        if pid not in pids:
            pids[pid] = {"count": 0, "pusi": 0, "tsc": tsc}
        pids[pid]["count"] += 1
        if pusi:
            pids[pid]["pusi"] += 1

        # Skip adaptation field only
        ps = 4
        if afc == 2:  # adaptation only
            continue
        if afc == 3:  # adaptation + payload
            af_len = pkt[4]
            ps = 5 + af_len

        payload = pkt[ps:]

        # PAT (PID 0)
        if pid == 0 and pusi:
            # Parse PAT
            pointer = payload[0]
            section = payload[1 + pointer:]
            table_id = section[0]
            section_len = ((section[1] & 0x0F) << 8) | section[2]
            print(f"\n=== PAT ===")
            print(f"  table_id=0x{table_id:02x} section_len={section_len}")
            # Programs start at offset 8, each 4 bytes
            prog_start = 8
            prog_end = 3 + section_len - 4  # minus CRC
            for j in range(prog_start, min(prog_end, len(section)) - 3, 4):
                prog_num = ((section[j] & 0xFF) << 8) | section[j+1]
                pmt_pid = ((section[j+2] & 0x1F) << 8) | section[j+3]
                if prog_num > 0:
                    print(f"  Program {prog_num} -> PMT PID 0x{pmt_pid:04x}")

        # PMT
        if pusi and payload[0] == 0x00:  # could be PMT
            # Check if it's a section
            if len(payload) > 3 and payload[1] in [0x02, 0x00]:  # PMT or PAT
                pointer = payload[0]
                section = payload[1 + pointer:]
                table_id = section[0]
                if table_id == 0x02:  # PMT
                    section_len = ((section[1] & 0x0F) << 8) | section[2]
                    print(f"\n=== PMT (PID 0x{pid:04x}) ===")
                    print(f"  table_id=0x{table_id:02x} section_len={section_len}")
                    pcrl = ((section[8] & 0x1F) << 8) | section[9]
                    print(f"  PCR PID: 0x{pcrl:04x}")
                    info_len = ((section[10] & 0x0F) << 8) | section[11]
                    print(f"  Program info length: {info_len}")
                    # Parse streams
                    j = 12 + info_len
                    while j < len(section) - 4:
                        stream_type = section[j]
                        es_pid = ((section[j+1] & 0x1F) << 8) | section[j+2]
                        es_info_len = ((section[j+3] & 0x0F) << 8) | section[j+4]
                        type_name = {
                            0x1B: "H.264 Video",
                            0x24: "H.265 Video",
                            0x0F: "AAC Audio",
                            0x03: "MP3 Audio",
                            0x02: "MPEG2 Video",
                            0x04: "MPEG2 Audio",
                            0x06: "Private/PES",
                        }.get(stream_type, f"Type 0x{stream_type:02x}")
                        print(f"  Stream: {type_name} PID=0x{es_pid:04x} info_len={es_info_len}")
                        if stream_type in [0x1B, 0x24, 0x02]:
                            video_pids.add(es_pid)
                        elif stream_type in [0x0F, 0x03, 0x04]:
                            audio_pids.add(es_pid)
                        # Print ES info
                        k = j + 5
                        while k < j + 5 + es_info_len:
                            tag = section[k]
                            l = section[k+1]
                            data_bytes = section[k+2:k+2+l]
                            print(f"    Tag 0x{tag:02x} len={l}: {data_bytes.hex()}")
                            k += 2 + l
                        j += 5 + es_info_len

    return pids, video_pids, audio_pids

pids, v_pids, a_pids = parse_ts_packets(data, 500)

print(f"\n=== PID Summary ===")
for pid, info in sorted(pids.items()):
    print(f"  PID 0x{pid:04x}: pkts={info['count']} pusi={info['pusi']} tsc={info['tsc']}")

print(f"\nVideo PIDs: {['0x{:04x}'.format(p) for p in v_pids]}")
print(f"Audio PIDs: {['0x{:04x}'.format(p) for p in a_pids]}")

# Check PES payloads of video and audio PIDs
print(f"\n=== PES Payload Analysis ===")
for pid_set, label in [(v_pids, "Video"), (a_pids, "Audio")]:
    for pid in pid_set:
        print(f"\n--- {label} PID 0x{pid:04x} ---")
        for i in range(min(n := len(data) // 188, 500)):
            pkt = data[i*188:(i+1)*188]
            if pkt[0] != 0x47:
                continue
            p = ((pkt[1] & 0x1F) << 8) | pkt[2]
            if p != pid:
                continue
            pusi = (pkt[1] >> 6) & 1
            if not pusi:
                continue
            afc = (pkt[3] >> 4) & 0x3
            ps = 4
            if afc == 2 or afc == 3:
                ps = 5 + pkt[4]
            pes = pkt[ps:]
            print(f"  PES first 32B: {pes[:32].hex()}")
            if pes[0] == 0x00 and pes[1] == 0x00 and pes[2] == 0x01:
                stream_id = pes[3]
                pes_len = ((pes[4] & 0xFF) << 8) | pes[5]
                print(f"  Stream ID: 0x{stream_id:02x} PES len: {pes_len}")
                # Skip PES header
                hdr_len = pes[8]
                payload_start = 9 + hdr_len
                nal_data = pes[payload_start:]
                print(f"  Payload first 32B: {nal_data[:32].hex()}")
                # Check for NAL start codes
                has_nal4 = b'\x00\x00\x00\x01' in nal_data[:100]
                has_nal3 = b'\x00\x00\x01' in nal_data[:100]
                print(f"  NAL start code 4-byte: {has_nal4}")
                print(f"  NAL start code 3-byte: {has_nal3}")
                if not has_nal4 and not has_nal3:
                    print("  *** NO NAL START CODES - PES PAYLOAD IS ENCRYPTED/OBFUSCATED ***")
            else:
                print(f"  Not a PES packet (no 000001 prefix)")
            break
