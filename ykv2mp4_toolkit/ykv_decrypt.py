"""YKV DRM 解密模块。

基于 RainVenturer/YKV-Cracker 的 key_unwrap.py, custom_b64.py,
config_drm.py, decryptor.py 整合简化。

DRM 密钥管线（来自 aliplayerVS.dll 逆向）：
    key_string = "part1,encryptR_server,copyright_key"

    第 1 层：
        K1 = hex(MD5(part1)[4:12])  # 16 字节 ASCII hex
        R2 = AES-ECB-Decrypt(K1, base64_decode(encryptR_server)[:16])
        r2_str = R2 截到第一个 null 字节

    第 2 层：
        K2 = hex(MD5(part1 || r2_str)[4:12])  # 16 字节 ASCII hex
        raw = AES-ECB-Decrypt(K2, base64_decode(copyright_key))

    自定义 Base64：
        key_material = custom_b64_decode(raw[:24])  # 24B → 18B
        # 字母表排除 'A'：B-Z(1-25), a-z(26-51), 0-9(52-61), +(62), /(63)

    AES 密钥：
        aes_key = key_material[:16]  # 16 字节 AES-128 密钥

    PES 解密：
        AES-ECB 解密 PES 连续 ES 数据（跨越 TS 包边界）
"""
from __future__ import annotations
import base64
import hashlib
from typing import List, Optional, Tuple
from Crypto.Cipher import AES

AES_BLOCK_SIZE = 16
TS_PACKET_SIZE = 188
TS_HEADER_SIZE = 4


# ---------------------------------------------------------------------------
# 密钥解包
# ---------------------------------------------------------------------------
def _md5_hex_key(data: bytes) -> bytes:
    """计算 MD5 并从字节 4..11 派生 AES-128 密钥（hex 字符串）。

    匹配 DLL 的密钥派生：
      MD5(输入) → hex 编码 MD5[4:12] (8 字节) → 16 字符 ASCII hex 字符串
      → 用这 16 个 ASCII 字节作为 AES-128 密钥
    """
    md5_digest = hashlib.md5(data).digest()
    hex_key = md5_digest[4:12].hex()  # 8字节 → 16字符 hex
    return hex_key.encode("ascii")


def _strlen(data: bytes) -> int:
    """查找第一个 null 字节的位置（C strlen 语义）。"""
    null_pos = data.find(b"\x00")
    return len(data) if null_pos < 0 else null_pos


def _unwrap_full(key_string: str) -> bytes:
    """执行完整的 2 层 AES 密钥解包，返回 part3 的完整解密数据。"""
    parts = key_string.split(",")
    if len(parts) != 3:
        raise ValueError(f"需要 3 个逗号分隔的部分，实际 {len(parts)} 个")

    part1, part2_b64, part3_b64 = [p.strip() for p in parts]
    if not part1 or not part2_b64 or not part3_b64:
        raise ValueError("三个部分都不能为空")

    # 第 1 层：解密 part2 得到 R2
    k1 = _md5_hex_key(part1.encode("ascii"))
    data2 = base64.b64decode(part2_b64)
    cipher1 = AES.new(k1, AES.MODE_ECB)
    r2_block = cipher1.decrypt(data2[:AES_BLOCK_SIZE])

    r2_len = _strlen(r2_block)
    r2 = r2_block[:r2_len] if r2_len > 0 else b""

    # 第 2 层：解密 part3 得到完整载荷
    k2 = _md5_hex_key(part1.encode("ascii") + r2)
    data3 = base64.b64decode(part3_b64)
    cipher2 = AES.new(k2, AES.MODE_ECB)
    return cipher2.decrypt(data3)


# ---------------------------------------------------------------------------
# 自定义 Base64 解码
# ---------------------------------------------------------------------------
def _build_decode_table() -> bytearray:
    """构建 256 字节解码查找表（匹配 sub_18064EDD0）。

    自定义字母表（排除 'A'）：
        B-Z  ->  1-25
        a-z  -> 26-51
        0-9  -> 52-61
        +    -> 62
        /    -> 63
    """
    table = bytearray(256)
    table[0x2B] = 62  # '+'
    table[0x2F] = 63  # '/'
    for i in range(10):
        table[0x30 + i] = 52 + i  # '0'-'9'
    for i in range(25):
        table[0x42 + i] = 1 + i  # 'B'-'Z'
    for i in range(26):
        table[0x61 + i] = 26 + i  # 'a'-'z'
    return table


_DECODE_TABLE = _build_decode_table()


def custom_b64_decode(data: bytes) -> bytes:
    """自定义 base64 解码，24 字节 → 18 字节。"""
    if len(data) != 24:
        raise ValueError(f"输入必须正好 24 字节，实际 {len(data)} 字节")

    decoded = bytearray(24)
    for i, b in enumerate(data):
        decoded[i] = _DECODE_TABLE[b]

    output = bytearray(18)
    out_idx = 0
    for i in range(0, 24, 4):
        a, b, c, d = decoded[i], decoded[i + 1], decoded[i + 2], decoded[i + 3]
        output[out_idx] = (a << 2) | (b >> 4)
        output[out_idx + 1] = ((b & 0x0F) << 4) | (c >> 2)
        output[out_idx + 2] = ((c & 0x03) << 6) | d
        out_idx += 3
    return bytes(output)


# ---------------------------------------------------------------------------
# 完整 DRM 设置
# ---------------------------------------------------------------------------
def setup_decryption(key_string: str) -> bytes:
    """配置 YKV 解密并返回 AES-128 密钥。

    匹配 aliplayerVS.dll 的 ConfigContextDrm (sub_18021B700)：
    1. 2 层 AES 解包 key_string → 完整 part3 载荷
    2. 对前 24 字节做 custom_b64_decode → 18 字节密钥材料
    3. 取前 16 字节作为 AES-128 密钥

    返回：
        16 字节 AES-128 密钥
    """
    full_payload = _unwrap_full(key_string)
    key_material = custom_b64_decode(full_payload[:24])
    return key_material[:16]


def find_part1(
    encryptR_server: str,
    copyright_key: str,
    progress_callback=None,
) -> Optional[str]:
    """暴力枚举 6 位数字 part1 值。

    有效的 part1 在用 K1 = MD5(part1)[4:12].hex() 作 AES-ECB 密钥
    解密 part2 时会产生全是 hex 字符 (0-9a-f) 的 16 字节 R2。
    随机 AES 输出全是 hex 字符的概率约 10⁻¹⁷，所以单一匹配保证正确。
    """
    data2 = base64.b64decode(encryptR_server)
    valid_hex = set(b"0123456789abcdef")
    for n in range(1_000_000):
        part1 = f"{n:06d}"
        k1_hex = hashlib.md5(part1.encode("ascii")).digest()[4:12].hex().encode("ascii")
        r2 = AES.new(k1_hex, AES.MODE_ECB).decrypt(data2[:16])
        if all(b in valid_hex for b in r2):
            return part1
        if n % 100_000 == 0 and n > 0 and progress_callback:
            progress_callback(n // 10_000)
    return None


# ---------------------------------------------------------------------------
# TS 解密
# ---------------------------------------------------------------------------
def _find_es_offset(packet: bytes) -> int:
    """找出 188 字节 TS 包内 ES 数据的起始偏移。

    只加密 PES payload（ES 数据），TS 头、adaptation field、
    PSI 表（PAT/PMT/SDT）和 PES 头都保持明文。
    """
    pid = ((packet[1] & 0x1F) << 8) | packet[2]
    pusi = (packet[1] >> 6) & 1
    afc = (packet[3] >> 4) & 3

    # 只有数据 PID (>= 0x0010 且 != 0x1FFF) 承载加密 ES
    if pid < 0x0010 or pid == 0x1FFF:
        return len(packet)
    if afc == 0 or afc == 2:
        return len(packet)

    payload_start = 4
    if afc == 3:
        payload_start = 5 + packet[4]
    if payload_start >= TS_PACKET_SIZE:
        return len(packet)

    if pusi:
        # PES 头：9 固定字节 + PES_header_data_length
        pes_hdr_data_len = packet[payload_start + 8]
        es_offset = payload_start + 9 + pes_hdr_data_len
    else:
        # 后续包 - 全部 payload 都是 ES 数据
        es_offset = payload_start
    return min(es_offset, TS_PACKET_SIZE)


def decrypt_ts_ecb(encrypted_data: bytes, aes_key: bytes) -> bytes:
    """使用 AES-ECB 解密 TS 数据。

    DLL 对整个 PES 包的连续 ES 数据（跨多个 TS 包）作为单一缓冲区解密。
    我们通过将每个 PES 的所有 TS 包的 ES 数据拼接起来、解密、再散回各包实现。

    TS 头、adaptation field、PSI 表、PES 头都保持明文。
    """
    if not encrypted_data:
        return b""
    cipher = AES.new(aes_key, AES.MODE_ECB)
    result = bytearray(encrypted_data)

    i = 0
    n_packets = len(encrypted_data) // TS_PACKET_SIZE
    while i < n_packets:
        off = i * TS_PACKET_SIZE
        pkt = encrypted_data[off:off + TS_PACKET_SIZE]
        pid = ((pkt[1] & 0x1F) << 8) | pkt[2]
        pusi = (pkt[1] >> 6) & 1
        if pid < 0x0010 or pid == 0x1FFF or not pusi:
            i += 1
            continue

        # 找到 PES 起点 - 收集这个 PES 的所有 ES 数据
        es_chunks = []
        es_positions = []
        j = i
        while j < n_packets:
            pkt_j = encrypted_data[j * TS_PACKET_SIZE:(j + 1) * TS_PACKET_SIZE]
            pid_j = ((pkt_j[1] & 0x1F) << 8) | pkt_j[2]
            pusi_j = (pkt_j[1] >> 6) & 1
            if pid_j != pid:
                break
            if j > i and pusi_j:
                break  # 下一个 PES 开始
            es_start = _find_es_offset(pkt_j)
            if es_start < TS_PACKET_SIZE:
                es_chunks.append(pkt_j[es_start:])
                es_positions.append((j, es_start))
            j += 1

        # 拼接 ES 数据，解密，散回
        if es_chunks:
            es_all = b"".join(es_chunks)
            aligned = (len(es_all) // 16) * 16
            if aligned > 0:
                decrypted = cipher.decrypt(es_all[:aligned])
                di = 0
                for pkt_idx, es_start in es_positions:
                    pkt_off = pkt_idx * TS_PACKET_SIZE
                    es_len = TS_PACKET_SIZE - es_start
                    copy_len = min(aligned - di, es_len)
                    if copy_len > 0:
                        result[pkt_off + es_start:pkt_off + es_start + copy_len] = (
                            decrypted[di:di + copy_len]
                        )
                        di += copy_len
        i = j  # 跳过这个 PES
    return bytes(result)
