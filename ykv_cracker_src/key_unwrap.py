# Copyright (C) 2026 RainVenturer
# SPDX-License-Identifier: GPL-3.0
"""3-layer AES key unwrapper for YKV decryption.

This implements the sub_180256020 function from aliplayerVS.dll,
which unwraps a comma-separated 3-part key string into a 16-byte AES session key.

Algorithm (verified from IDA decompilation of sub_180256020):
    Layer 1:
        1. Split key_string by "," into 3 parts
        2. MD5(part1_ascii) → 16 bytes
        3. Hex-encode MD5[4:12] (8 bytes) → 16-char ASCII hex string → K1
        4. Base64Decode(part2) → 18 bytes
        5. AES-ECB-Decrypt(K1, data[:16]) → R2 (first 16 bytes only)

    Layer 2:
        6. Find null terminator in R2 → extract R2 string
        7. MD5(R2_ascii) → 16 bytes
        8. Hex-encode MD5[4:12] (8 bytes) → 16-char ASCII hex string → K2
        9. Base64Decode(part3) → 33 bytes
        10. AES-ECB-Decrypt(K2, data) → SessionKey blocks
        11. Return first 16 bytes as AES session key

The hex encoding uses lowercase hex digits "0123456789abcdef", matching
the table at address 0x8A3F20 in aliplayerVS.dll.
"""
from __future__ import annotations

import base64
import hashlib

from Crypto.Cipher import AES

AES_BLOCK_SIZE = 16


def _md5_hex_key(data: bytes) -> bytes:
    """Compute MD5 and derive AES-128 key from bytes 4..11 as hex.

    This matches the DLL's key derivation:
      sub_69D460 (MD5 of input)
      → hex-encode MD5[4:12] (8 bytes) → 16-char ASCII hex string
      → use those 16 ASCII bytes as AES-128 key

    The hex table at 0x8A3F20 is "0123456789abcdef" (lowercase),
    which matches Python's bytes.hex() output.
    """
    md5_digest = hashlib.md5(data).digest()
    # MD5[4:12] → hex → 16 ASCII bytes
    hex_key = md5_digest[4:12].hex()
    return hex_key.encode("ascii")


def _strlen(data: bytes) -> int:
    """Find the position of the first null byte (C strlen semantics).

    Returns the index of the first 0x00 byte, or the length of the data
    if no null byte is found. This matches the DLL behavior:
        if (Src[0]) {
            do ++Size_2; while (Src[Size_2]);  // strlen
        }
    """
    null_pos = data.find(b"\x00")
    return len(data) if null_pos < 0 else null_pos


def key_unwrap(key_string: str) -> bytes:
    """Unwrap a 3-layer AES key string into raw key bytes.

    This implements the sub_180256020 function from aliplayerVS.dll.

    Algorithm (from IDA decompilation of sub_180256020):
        Layer 1:
            1. Split key_string by ',' into 3 parts
            2. MD5(part1) → 16 bytes
            3. Hex-encode MD5[4:12] (8 bytes) → 16-char ASCII hex string → K1
            4. Base64Decode(part2) → N bytes
            5. AES-ECB-Decrypt(K1, data[:16]) → R2 (first 16 bytes)

        Layer 2:
            6. Find null terminator in R2 → R2 string
            7. MD5(part1 + R2) → 16 bytes  (DLL appends R2 to part1 buffer)
            8. Hex-encode MD5[4:12] → K2
            9. Base64Decode(part3) → N bytes
            10. AES-ECB-Decrypt(K2, data) → raw blocks
            11. Find null terminator → return up to null

    Returns:
        Null-terminated bytes (the raw decrypted output of sub_256020).
        The caller must apply custom_b64_decode followed by aes_key_expand
        to derive the AES session key.

    Raises:
        ValueError: If the key_string format is invalid or decryption fails.
    """
    if not key_string:
        raise ValueError("key_string must not be empty")

    parts = key_string.split(",")
    if len(parts) != 3:
        raise ValueError(
            f"Expected 3 comma-separated parts, got {len(parts)}"
        )

    part1, part2_b64, part3_b64 = [p.strip() for p in parts]

    if not part1 or not part2_b64 or not part3_b64:
        raise ValueError("All three parts must be non-empty")

    # ---- Layer 1: Decrypt part2 to get R2 ----

    # Step 1-3: MD5(part1) → hex bytes 4-11 → AES key K1
    k1 = _md5_hex_key(part1.encode("ascii"))

    # Step 4: Base64 decode part2
    data2 = base64.b64decode(part2_b64)

    # Step 5: AES-ECB decrypt first 16 bytes
    cipher1 = AES.new(k1, AES.MODE_ECB)
    r2_block = cipher1.decrypt(data2[:AES_BLOCK_SIZE])

    # Extract R2 as null-terminated ASCII string
    r2_len = _strlen(r2_block)
    if r2_len == 0:
        # R2 is empty — MD5 of empty string will be used for K2
        r2 = b""
    else:
        r2 = r2_block[:r2_len]

    # ---- Layer 2: Decrypt part3 to get SessionKey ----

    # Step 7-8: MD5(part1 + R2) → hex bytes 4-11 → AES key K2
    #   DLL sub_CF480 appends R2 to the part1 buffer (overwrite+append semantics
    #   in the MSVC short-string). The resulting MD5 input is part1 concatenated
    #   with R2, NOT R2 alone.
    k2 = _md5_hex_key(part1.encode("ascii") + r2)

    # Step 9: Base64 decode part3
    data3 = base64.b64decode(part3_b64)

    # Step 10: AES-ECB decrypt all blocks
    cipher2 = AES.new(k2, AES.MODE_ECB)
    session_raw = cipher2.decrypt(data3)

    # Step 11: Return null-terminated portion (DLL uses strlen(), caller
    # does custom_b64_decode + aes_key_expand on this result)
    null_pos = session_raw.find(b"\x00")
    if null_pos >= 0:
        return session_raw[:null_pos]
    return session_raw


def key_unwrap_with_validation(key_string: str) -> dict:
    """Unwrap key string with detailed validation and diagnostics.

    Performs the same unwrap as key_unwrap() but also checks the DLL's
    internal validation conditions and returns intermediate values
    for debugging.

    Returns:
        dict with keys:
            - session_key (bytes): 16-byte AES session key
            - r2_hex (str): hex-encoded R2 from layer 1
            - k1_hex_key (str): hex key string used for layer 1
            - k2_hex_key (str): hex key string used for layer 2
            - r2_error (bool): whether "r2 error" condition was met
            - key_error (bool): whether "key error" condition was met
    """
    parts = key_string.split(",")
    part1, part2_b64, part3_b64 = parts

    # Layer 1
    k1 = _md5_hex_key(part1.encode("ascii"))
    data2 = base64.b64decode(part2_b64)
    cipher1 = AES.new(k1, AES.MODE_ECB)
    r2_block = cipher1.decrypt(data2[:AES_BLOCK_SIZE])

    r2_len = _strlen(r2_block)
    r2 = r2_block[:r2_len] if r2_len > 0 else b""

    # R2 error check: Src[6] && Src[7] && Src[8..15] all non-zero
    r2_error = False
    if len(r2_block) >= 16:
        if r2_block[6] and r2_block[7]:
            if all(r2_block[i] for i in range(8, 16)):
                r2_error = True

    # Layer 2: MD5(part1 + R2) per DLL sub_CF480 append semantics
    k2 = _md5_hex_key(part1.encode("ascii") + r2)
    data3 = base64.b64decode(part3_b64)
    cipher2 = AES.new(k2, AES.MODE_ECB)
    session_raw = cipher2.decrypt(data3)

    # Find null terminator (DLL strlen behavior when output to caller)
    null_pos = session_raw.find(b"\x00")
    session_full = session_raw[:null_pos] if null_pos >= 0 else session_raw

    # Key error check: Src[24..31] all non-zero
    key_error = False
    if len(session_raw) >= 32:
        if all(session_raw[i] for i in range(24, 32)):
            key_error = True

    return {
        "session_key": session_full,
        "r2_hex": r2_block.hex(),
        "r2_string": r2.decode("ascii", errors="replace"),
        "k1_hex_key": k1.decode("ascii"),
        "k2_hex_key": k2.decode("ascii"),
        "r2_error": r2_error,
        "key_error": key_error,
    }


def find_part1(
    encryptR_server: str,
    copyright_key: str,
    progress_callback=None,
) -> str | None:
    """Brute-force the 6-digit part1 value.

    A valid part1 produces a 16-byte ASCII hex string R2 when ``part2`` is
    AES-ECB-decrypted with K1 = MD5(part1)[4:12].hex.  Random AES output
    has only ~(22/256)¹⁶ ≈ 10⁻¹⁷ chance of being all hex chars, so the
    single match is guaranteed correct.

    Args:
        encryptR_server: base64 part2 from YKV JSON.
        copyright_key: base64 part3 from YKV JSON.
        progress_callback: optional ``callable(percent: int)``.

    Returns:
        The 6-digit part1 string, or ``None`` if not found.
    """
    import base64
    import hashlib

    from Crypto.Cipher import AES

    data2 = base64.b64decode(encryptR_server)
    valid_hex = set(b'0123456789abcdef')

    for n in range(1_000_000):
        part1 = f"{n:06d}"
        k1_hex = hashlib.md5(part1.encode("ascii")).digest()[4:12].hex().encode("ascii")
        r2 = AES.new(k1_hex, AES.MODE_ECB).decrypt(data2[:16])

        if all(b in valid_hex for b in r2):
            return part1

        if n % 100_000 == 0 and n > 0 and progress_callback:
            progress_callback(n // 10_000)

    return None
