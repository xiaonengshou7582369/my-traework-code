"""Carefully analyze PES payload of video PID."""
import os, json
from pathlib import Path
from urllib.parse import unquote

YKV = Path(r"D:\Youku Files\download\沧元图\第1集 所有妖怪都得死-国语.ykv")
YK_HEADER = 34
VIDEO_PID = 0x0100
AUDIO_PID = 0x0101

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

# Read segment 1 (small, 560K - likely intro)
seg = ts_segs[0]
off = int(seg["offset"]) + YK_HEADER
size = int(seg["size"]) - YK_HEADER
with YKV.open("rb") as f:
    f.seek(off)
    data = f.read(size)

print(f"Segment {seg['name']}: {size} bytes, {size//188} packets")

# Collect all video PES packets and concatenate payloads
video_pes_data = b""
audio_pes_data = b""
n = len(data) // 188

for i in range(n):
    pkt = data[i*188:(i+1)*188]
    if pkt[0] != 0x47:
        continue
    pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
    pusi = (pkt[1] >> 6) & 1
    afc = (pkt[3] >> 4) & 0x3
    tsc = (pkt[3] >> 6) & 0x3

    ps = 4
    if afc == 2:  # adaptation only
        continue
    if afc == 3:  # adaptation + payload
        af_len = pkt[4]
        ps = 5 + af_len

    payload = pkt[ps:]
    if len(payload) == 0:
        continue

    if pid == VIDEO_PID:
        if pusi:
            # Start of new PES
            if video_pes_data:
                pass  # already have data, will be overwritten
            # Parse PES header
            if payload[0] == 0x00 and payload[1] == 0x00 and payload[2] == 0x01:
                stream_id = payload[3]
                pes_len = ((payload[4] & 0xFF) << 8) | payload[5]
                flags1 = payload[6]
                flags2 = payload[7]
                hdr_len = payload[8]
                payload_data = payload[9 + hdr_len:]
                video_pes_data = payload_data
            else:
                video_pes_data = payload
        else:
            # Continuation
            video_pes_data += payload

    if pid == AUDIO_PID:
        if pusi:
            if payload[0] == 0x00 and payload[1] == 0x00 and payload[2] == 0x01:
                hdr_len = payload[8]
                audio_pes_data = payload[9 + hdr_len:]
            else:
                audio_pes_data = payload
        else:
            audio_pes_data += payload

print(f"\nVideo PES total: {len(video_pes_data)} bytes")
print(f"Audio PES total: {len(audio_pes_data)} bytes")

# Analyze video PES
print(f"\n=== Video PES first 100 bytes ===")
print(video_pes_data[:100].hex())
print(f"\n=== Looking for NAL start codes (00 00 00 01 or 00 00 01) ===")
# Search entire payload
for i in range(len(video_pes_data) - 4):
    if video_pes_data[i] == 0 and video_pes_data[i+1] == 0:
        if video_pes_data[i+2] == 1:
            nal_type = video_pes_data[i+3]
            print(f"  Found 3-byte NAL at offset {i}: type=0x{nal_type:02x}")
            break
        elif video_pes_data[i+2] == 0 and video_pes_data[i+3] == 1:
            nal_type = video_pes_data[i+4]
            print(f"  Found 4-byte NAL at offset {i}: type=0x{nal_type:02x}")
            break
else:
    print("  NO NAL start codes found - payload IS encrypted/obfuscated")
    # Check entropy
    from collections import Counter
    c = Counter(video_pes_data[:1000])
    print(f"  Byte distribution (first 1000B): {len(c)} unique bytes")
    print(f"  Most common: {c.most_common(5)}")
    # Check if it looks random (high entropy)
    import math
    entropy = -sum((count/1000) * math.log2(count/1000) for count in c.values())
    print(f"  Entropy: {entropy:.2f} bits/byte (8.0 = random)")

# Analyze audio PES
print(f"\n=== Audio PES first 100 bytes ===")
print(audio_pes_data[:100].hex())
# Check for ADTS header (0xFF F0/F1)
if audio_pes_data[0] == 0xFF and (audio_pes_data[1] & 0xF0) == 0xF0:
    print("  ADTS header found - audio NOT encrypted")
else:
    print("  No ADTS header - audio might be encrypted")
    from collections import Counter
    import math
    c = Counter(audio_pes_data[:1000])
    entropy = -sum((count/1000) * math.log2(count/1000) for count in c.values())
    print(f"  Entropy: {entropy:.2f} bits/byte")

# Check the first PES packet more carefully
print(f"\n=== First video PES packet (raw) ===")
for i in range(n):
    pkt = data[i*188:(i+1)*188]
    if pkt[0] != 0x47: continue
    pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
    if pid != VIDEO_PID: continue
    pusi = (pkt[1] >> 6) & 1
    if not pusi: continue
    print(f"Packet {i}: PUSI=1")
    print(f"  Full packet hex: {pkt.hex()}")
    afc = (pkt[3] >> 4) & 0x3
    ps = 4
    if afc == 3:
        af_len = pkt[4]
        ps = 5 + af_len
        print(f"  Adaptation field: {af_len} bytes")
    pes = pkt[ps:]
    print(f"  PES data ({len(pes)}B): {pes.hex()}")
    if pes[0] == 0 and pes[1] == 0 and pes[2] == 1:
        print(f"  Stream ID: 0x{pes[3]:02x}")
        print(f"  PES packet length: {((pes[4]<<8)|pes[5])}")
        print(f"  Flags: {pes[6]:02x} {pes[7]:02x}")
        print(f"  Header len: {pes[8]}")
        hdr = pes[9:9+pes[8]]
        print(f"  Header bytes: {hdr.hex()}")
        payload = pes[9+pes[8]:]
        print(f"  Payload ({len(payload)}B): {payload.hex()}")
    break

# Try: maybe the video uses HEVC with length-prefixed NAL units (not start codes)
# HEVC in MP4 uses 4-byte big-endian length prefix
print(f"\n=== Check for length-prefixed NAL units ===")
first4 = int.from_bytes(video_pes_data[:4], 'big')
print(f"First 4 bytes as big-endian: {first4} (0x{first4:08x})")
if 0 < first4 < len(video_pes_data):
    print(f"  Might be length prefix! Next byte: 0x{video_pes_data[4]:02x}")
    # HEVC NAL type is (byte >> 1) & 0x3F
    nal_type = (video_pes_data[4] >> 1) & 0x3F
    print(f"  Possible HEVC NAL type: {nal_type}")
else:
    print(f"  Not a valid length prefix")
