# Copyright (C) 2026 RainVenturer
# SPDX-License-Identifier: GPL-3.0
"""AES-ECB decryption for YKV files.

Per the aliplayerVS.dll reverse engineering (sub_64F740 / tbEncryptionInit),
the TS decryption uses AES-ECB (not CBC) with a 4×4 matrix transposition
on each 16-byte block.  The ``aes_ecb_decrypt_block`` function from
``aes_core.py`` already handles the transposition — it matches the DLL's
``sub_64F240`` byte-for-byte.
"""
from __future__ import annotations
import base64
import hashlib
import warnings
from typing import List, Optional, Tuple

from Crypto.Cipher import AES

TS_PACKET_SIZE = 188
TS_HEADER_SIZE = 4


def _normalise_b64(value: str) -> bytes:
    """Normalise and decode a potentially URL-safe base64 string."""
    padded = value.strip().replace('-', '+').replace('_', '/')
    while len(padded) % 4:
        padded += '='
    try:
        return base64.b64decode(padded)
    except Exception as exc:
        raise ValueError(f"Failed to decode base64 value: {exc}") from exc


def derive_key(r1_random: str) -> Tuple[bytes, bytes]:
    """
    Derive AES-128 key and IV from R1Random value.

    .. deprecated::
        Use :func:`decrypt_with_key_string` instead.  This function treats
        the ``R1Random`` field from the YKV JSON trailer (which is actually
        ``clientR1``) as a raw AES key — an old placeholder approach that
        does **not** match the real ConfigContextDrm pipeline.

    R1Random is a base64 string (typically 24 chars, URL-safe variant allowed).
    Decoded -> 18 bytes. First 16 = AES key.
    IV defaults to zero bytes (call find_valid_iv for automatic IV discovery).
    """
    warnings.warn(
        "derive_key is deprecated. Use decrypt_with_key_string instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if not r1_random:
        raise ValueError("R1Random value is empty")

    raw = _normalise_b64(r1_random)

    if len(raw) < 16:
        raise ValueError(
            f"Decoded key too short: {len(raw)} bytes, need >= 16"
        )

    key = raw[:16]
    iv = b'\x00' * 16

    return key, iv


def decrypt_with_key_string(
    encrypted_data: bytes,
    key_string: str,
    drm_type: int = 2,
) -> bytes:
    """Decrypt TS data using the real ConfigContextDrm pipeline.

    This is the production decryption path matching aliplayerVS.dll:

    1. ``setup_decryption(drm_type, key_string)`` → 11 round keys
    2. ``round_keys[0]`` = original AES-128 key (column-major)
    3. PyCrypto AES-ECB per 16‑byte block on TS payload (184 bytes/pkt)

    PyCrypto AES‑ECB with the *original* (column‑major) key is equivalent
    to the DLL's transposed‑data + transposed‑keys approach — the two
    transpositions cancel out.

    The DLL uses **ECB mode** (not CBC) — each 16‑byte block is decrypted
    independently with no IV and no chaining.

    Args:
        encrypted_data: Raw encrypted TS stream (188‑byte aligned, segment
                        headers already stripped by the parser).
        key_string: Comma‑separated ``"part1,encryptR_server,copyright_key"``
                    as received by ``ConfigContextDrm`` in the DLL.
        drm_type: DRM type (2 for standard copyrightDRM playback).

    Returns:
        Decrypted TS data.

    Raises:
        ValueError: If ``key_string`` is empty or malformed.
    """
    if not key_string or not key_string.strip():
        raise ValueError("key_string is empty")

    from ykv_cracker.config_drm import setup_decryption

    round_keys_std = setup_decryption(drm_type, key_string)
    aes_key = round_keys_std[0]  # original AES-128 key (column-major)

    return decrypt_ts_ecb(encrypted_data, aes_key)


def _find_es_offset(packet: bytes) -> int:
    """Find the ES data start offset within a 188-byte TS packet.

    Matches the DLL's encryption scheme: only the PES payload (elementary
    stream data) is encrypted — TS headers, adaptation fields, PSI tables,
    and PES packet headers are left in the clear.

    Returns:
        Byte offset where ES data starts, or ``len(packet)`` if this
        packet carries no decryptable ES data.
    """
    pid = ((packet[1] & 0x1f) << 8) | packet[2]
    pusi = (packet[1] >> 6) & 1
    afc = (packet[3] >> 4) & 3

    # Only data PIDs (>= 0x0010 and != 0x1FFF) carry encrypted ES
    if pid < 0x0010 or pid == 0x1FFF:
        return len(packet)
    if afc == 0 or afc == 2:
        return len(packet)

    # Adaptation field consumes bytes after the 4-byte header
    payload_start = 4
    if afc == 3:
        payload_start = 5 + packet[4]

    if payload_start >= TS_PACKET_SIZE:
        return len(packet)

    if pusi:
        # PES header: 9 fixed bytes + PES_header_data_length
        pes_hdr_data_len = packet[payload_start + 8]
        es_offset = payload_start + 9 + pes_hdr_data_len
    else:
        # Continuation packet — all payload bytes are ES data
        es_offset = payload_start

    return min(es_offset, TS_PACKET_SIZE)


def decrypt_ts_ecb(
    encrypted_data: bytes,
    aes_key: bytes,
) -> bytes:
    """Decrypt TS data using PyCrypto AES-ECB.

    Mirrors the DLL's behaviour where ``DecryptionCopyrightDRM``
    (sub_6413E0) applies AES-ECB to each demuxed AVPacket's data.

    The DLL decrypts the **contiguous ES data** of an entire PES packet
    (spanning multiple TS packets) as a single buffer.  We replicate this
    by concatenating ES data across all TS packets of each PES, decrypting
    the concatenated buffer, and then scattering the decrypted bytes back
    into the output TS packets.

    TS headers, adaptation fields, PSI tables (PAT/PMT/SDT), and PES packet
    headers are all left in the clear.

    Args:
        encrypted_data: Raw encrypted TS stream (188‑byte aligned, segment
                        headers already stripped by the parser).
        aes_key: 16‑byte AES-128 key.

    Returns:
        Decrypted TS data.
    """
    if not encrypted_data:
        return b''

    cipher = AES.new(aes_key, AES.MODE_ECB)

    # Build output buffer and track ES regions per packet
    result = bytearray(encrypted_data)

    # Group TS packets into PES units: each PUSI=1 data PID starts a new PES
    i = 0
    n_packets = len(encrypted_data) // TS_PACKET_SIZE
    while i < n_packets:
        off = i * TS_PACKET_SIZE
        pkt = encrypted_data[off:off + TS_PACKET_SIZE]
        pid = ((pkt[1] & 0x1f) << 8) | pkt[2]
        pusi = (pkt[1] >> 6) & 1

        if pid < 0x0010 or pid == 0x1FFF or not pusi:
            i += 1
            continue

        # Found a PES start — collect all ES data from this PES
        es_chunks = []
        es_positions = []
        j = i
        while j < n_packets:
            pkt_j = encrypted_data[j * TS_PACKET_SIZE:(j + 1) * TS_PACKET_SIZE]
            pid_j = ((pkt_j[1] & 0x1f) << 8) | pkt_j[2]
            pusi_j = (pkt_j[1] >> 6) & 1

            # Same PID? If PUSI, only include if this is the START PES packet
            if pid_j != pid:
                break
            if j > i and pusi_j:
                break  # next PES starts

            es_start = _find_es_offset(pkt_j)
            if es_start < TS_PACKET_SIZE:
                es_chunks.append(pkt_j[es_start:])
                es_positions.append((j, es_start))
            j += 1

        # Concatenate ES data, decrypt, scatter back
        if es_chunks:
            es_all = b''.join(es_chunks)
            aligned = (len(es_all) // 16) * 16
            if aligned > 0:
                decrypted = cipher.decrypt(es_all[:aligned])
                # Scatter decrypted bytes back into result
                di = 0
                for pkt_idx, es_start in es_positions:
                    pkt_off = pkt_idx * TS_PACKET_SIZE
                    es_end = es_start + (len(encrypted_data[pkt_off + es_start:pkt_off + TS_PACKET_SIZE]))
                    copy_len = min(aligned - di, es_end - es_start)
                    if copy_len > 0:
                        result[pkt_off + es_start:pkt_off + es_start + copy_len] = decrypted[di:di + copy_len]
                        di += copy_len

        i = j  # skip past this PES

    return bytes(result)


def find_valid_iv_for_key(encrypted_data: bytes, key: bytes) -> bytes:
    """Discover a working IV for a given AES key by checking TS sync bytes.

    Tries common IV variants (zero, key-as-IV, hashes).  Returns the first
    IV that produces valid 0x47 sync bytes or zero-IV as fallback.
    """
    variants: list[Tuple[bytes, str]] = [
        (b'\x00' * 16, "zero_iv"),
        (key, "key_as_iv"),
        (hashlib.sha256(key).digest()[:16], "sha256_key"),
        (hashlib.md5(key).digest()[:16], "md5_key"),
    ]

    sample = encrypted_data[:188 * 10]
    for iv, _name in variants:
        decrypted = decrypt_ts(sample, key, iv)
        valid = True
        for i in range(0, min(len(decrypted), 1880), 188):
            if i < len(decrypted) and decrypted[i] != 0x47:
                valid = False
                break
        if valid:
            return iv

    return b'\x00' * 16  # fallback


def try_iv_variants(r1_random: str) -> list[Tuple[bytes, bytes, str]]:
    """Try multiple IV derivation approaches and return all candidates."""
    key, _ = derive_key(r1_random)
    raw = _normalise_b64(r1_random)

    variants: list[Tuple[bytes, bytes, str]] = [
        # 1. Zero IV (most common default)
        (key, b'\x00' * 16, "zero_iv"),
        # 2. Key itself as IV
        (key, key, "key_as_iv"),
        # 3. SHA-256 of key, truncated to 16 bytes
        (key, hashlib.sha256(key).digest()[:16], "sha256_key"),
        # 4. MD5 of key
        (key, hashlib.md5(key).digest()[:16], "md5_key"),
        # 5. SHA-256 of the original r1 string
        (key, hashlib.sha256(r1_random.encode()).digest()[:16], "sha256_r1"),
    ]

    # 6. Remaining bytes from raw (bytes 16-31) if available
    if len(raw) >= 32:
        variants.append((key, raw[16:32], "raw_extended"))

    return variants


def decrypt_ts(encrypted_data: bytes, key: bytes, iv: bytes) -> bytes:
    """
    Decrypt TS data using AES-CBC.

    TS packets are 188 bytes. The first 4 bytes = header (unencrypted/kept).
    Remaining 184 bytes are encrypted in AES-CBC mode.
    A FRESH AES cipher is created for each packet, resetting to the original IV,
    because each TS packet is encrypted independently.
    """
    if not encrypted_data:
        return b''

    result = bytearray()

    offset = 0
    while offset < len(encrypted_data):
        chunk = encrypted_data[offset:offset + TS_PACKET_SIZE]
        if len(chunk) < TS_PACKET_SIZE:
            # Partial packet at the end
            if len(chunk) > TS_HEADER_SIZE:
                header = chunk[:TS_HEADER_SIZE]
                payload = chunk[TS_HEADER_SIZE:]
                aligned_len = (len(payload) // 16) * 16
                if aligned_len > 0:
                    cipher = AES.new(key, AES.MODE_CBC, iv)
                    decrypted = cipher.decrypt(payload[:aligned_len])
                    result.extend(header)
                    result.extend(decrypted)
                    result.extend(payload[aligned_len:])
                else:
                    result.extend(chunk)
            else:
                result.extend(chunk)
            break

        header = chunk[:TS_HEADER_SIZE]
        payload = chunk[TS_HEADER_SIZE:]

        # Fresh cipher per packet — IV is reset for each TS packet
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # Align payload to 16-byte AES block boundary
        aligned_len = (len(payload) // 16) * 16
        if aligned_len > 0:
            decrypted = cipher.decrypt(payload[:aligned_len])
        else:
            decrypted = b''

        result.extend(header)
        result.extend(decrypted)
        result.extend(payload[aligned_len:])  # keep any remaining bytes as-is
        offset += TS_PACKET_SIZE

    return bytes(result)


def find_valid_iv(ykv_file: object) -> Tuple[bytes, bytes]:
    """
    Try different IV derivations and return the one that produces
    valid TS data (has proper 0x47 sync bytes throughout).

    Returns (key, iv) for the first working variant.
    If none works, returns the first variant anyway as a fallback.
    """
    r1: str = getattr(ykv_file, 'r1_random', '')
    if not r1:
        # No R1Random — return zero key/IV as fallback
        return b'\x00' * 16, b'\x00' * 16

    variants = try_iv_variants(r1)

    # Use a sample of encrypted data to validate (first 10 packets)
    encrypted_data: bytes = getattr(ykv_file, 'encrypted_data', b'')
    sample = encrypted_data[:188 * 10]

    for key, iv, name in variants:
        decrypted = decrypt_ts(sample, key, iv)
        # Check TS sync bytes at expected positions
        valid = True
        for i in range(0, len(decrypted), TS_PACKET_SIZE):
            if i < len(decrypted) and decrypted[i] != 0x47:
                valid = False
                break
        if valid:
            return key, iv

    # Fallback: return first variant
    key, iv, _ = variants[0]
    return key, iv


def decrypt_ykv(ykv_file: object) -> bytes:
    """
    Fully decrypt a parsed YKVFile and return the decrypted TS data.

    Automatically discovers the correct IV by checking sync-byte validity.
    """
    key, iv = find_valid_iv(ykv_file)
    encrypted_data: bytes = getattr(ykv_file, 'encrypted_data', b'')
    return decrypt_ts(encrypted_data, key, iv)
