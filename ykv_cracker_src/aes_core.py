# Copyright (C) 2026 RainVenturer
# SPDX-License-Identifier: GPL-3.0
"""AES-ECB single-block decryption matching aliplayerVS.dll sub_64F240.

This module implements the exact AES-ECB block decryption algorithm found
in aliplayerVS.dll (sub_64F240 at offset 0x64F240). The implementation
uses standard AES S-boxes and operations but applies a byte transpose to
match the DLL's internal row-major state layout.

Key differences from standard AES-ECB:
1. Input/output are in standard column-major byte order (like all AES)
2. Internal state is transposed to row-major (DLL convention)
3. Round keys must be provided in row-major transposed format
4. The core algorithm (S-box, InvShiftRows, InvMixColumns, AddRoundKey) is standard
"""

from __future__ import annotations

from typing import List

# ---------------------------------------------------------------------------
# S-box: standard AES forward S-box (256 bytes)
# Source: aliplayerVS.dll byte_B25590 @ 0xB25590
# Verified against FIPS-197: ✓
# ---------------------------------------------------------------------------
S_BOX = bytes([
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
    0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0,
    0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc,
    0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a,
    0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0,
    0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b,
    0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85,
    0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5,
    0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17,
    0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88,
    0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c,
    0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9,
    0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6,
    0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e,
    0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94,
    0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68,
    0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
])

# ---------------------------------------------------------------------------
# Inverse S-box: standard AES inverse S-box (256 bytes)
# Source: aliplayerVS.dll off_B25690 @ 0xB25690
# Verified against FIPS-197: ✓
# ---------------------------------------------------------------------------
INV_S_BOX = bytes([
    0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38,
    0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
    0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87,
    0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
    0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d,
    0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
    0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2,
    0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
    0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16,
    0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
    0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda,
    0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
    0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a,
    0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
    0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02,
    0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
    0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea,
    0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
    0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85,
    0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
    0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89,
    0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
    0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20,
    0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
    0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31,
    0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
    0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d,
    0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
    0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0,
    0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
    0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26,
    0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d,
])


# ---------------------------------------------------------------------------
# GF(2^8) multiplication helpers
# ---------------------------------------------------------------------------

def _gf_mul(a: int, b: int) -> int:
    """Multiply two bytes in GF(2^8) with AES irreducible polynomial 0x11b.

    Args:
        a: First byte (0-255).
        b: Second byte (0-255).

    Returns:
        Product in GF(2^8).
    """
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        a <<= 1
        if a & 0x100:
            a ^= 0x11B
        b >>= 1
    return result


# Precomputed InvMixColumns multiplication tables for {9, 11, 13, 14}.
# These match the T-box tables at byte_B24590 in aliplayerVS.dll.
_GF_MUL_9 = bytes(_gf_mul(i, 9) for i in range(256))
_GF_MUL_11 = bytes(_gf_mul(i, 11) for i in range(256))
_GF_MUL_13 = bytes(_gf_mul(i, 13) for i in range(256))
_GF_MUL_14 = bytes(_gf_mul(i, 14) for i in range(256))


# ---------------------------------------------------------------------------
# State transformations
# ---------------------------------------------------------------------------

def transpose(state: List[int]) -> List[int]:
    """Transpose a 16-byte AES state between column-major and row-major.

    This is a self-inverse operation: transpose(transpose(x)) == x.

    Column-major (standard AES):  [c0r0, c0r1, c0r2, c0r3, c1r0, ...]
    Row-major (DLL internal):     [r0c0, r0c1, r0c2, r0c3, r1c0, ...]

    Args:
        state: 16-byte state as a list of integers.

    Returns:
        Transposed 16-byte state.
    """
    return [
        state[0], state[4], state[8], state[12],   # row 0
        state[1], state[5], state[9], state[13],    # row 1
        state[2], state[6], state[10], state[14],   # row 2
        state[3], state[7], state[11], state[15],   # row 3
    ]


def inv_shift_rows(state: List[int]) -> List[int]:
    """Apply InvShiftRows on a row-major state (16 bytes).

    Row 0: no shift
    Row 1: rotate right by 1 byte
    Row 2: rotate right by 2 bytes
    Row 3: rotate right by 3 bytes

    Implemented via 32-bit little-endian word rotations to match the DLL.

    Args:
        state: 16-byte state in row-major order.

    Returns:
        State after InvShiftRows.
    """
    result = list(state)
    # Row 0: unchanged (indices 0..3)

    # Row 1: right rotate 1 byte → [d, a, b, c] (indices 4..7)
    # Equivalent to RotateLeft_8 on LE word: [a,b,c,d] → [d,a,b,c]
    result[4], result[5], result[6], result[7] = (
        state[7], state[4], state[5], state[6]
    )

    # Row 2: right rotate 2 bytes → [c, d, a, b] (indices 8..11)
    # Equivalent to RotateLeft_16 on LE word: [a,b,c,d] → [c,d,a,b]
    result[8], result[9], result[10], result[11] = (
        state[10], state[11], state[8], state[9]
    )

    # Row 3: right rotate 3 bytes → [b, c, d, a] (indices 12..15)
    # Equivalent to RotateRight_8 on LE word: [a,b,c,d] → [b,c,d,a]
    result[12], result[13], result[14], result[15] = (
        state[13], state[14], state[15], state[12]
    )

    return result


def inv_sub_bytes(state: List[int]) -> List[int]:
    """Apply InvSubBytes using the inverse S-box.

    Each byte in the state is replaced by INV_S_BOX[byte].

    Args:
        state: 16-byte state.

    Returns:
        State after InvSubBytes.
    """
    return [INV_S_BOX[b] for b in state]


def inv_mix_columns(state: List[int]) -> List[int]:
    """Apply InvMixColumns on a row-major state.

    In row-major layout, each column consists of bytes at positions
    [c, c+4, c+8, c+12] for column index c in 0..3.

    The InvMixColumns matrix multiplication:
    [b0]   [14, 11, 13, 9 ]  [a0]
    [b1] = [9,  14, 11, 13]  [a1]
    [b2]   [13, 9,  14, 11]  [a2]
    [b3]   [11, 13, 9,  14]  [a3]

    Args:
        state: 16-byte state in row-major order.

    Returns:
        State after InvMixColumns.
    """
    result = list(state)
    for c in range(4):
        a0 = state[c]
        a1 = state[c + 4]
        a2 = state[c + 8]
        a3 = state[c + 12]

        result[c]      = _GF_MUL_14[a0] ^ _GF_MUL_11[a1] ^ _GF_MUL_13[a2] ^ _GF_MUL_9[a3]
        result[c + 4]  = _GF_MUL_9[a0]  ^ _GF_MUL_14[a1] ^ _GF_MUL_11[a2] ^ _GF_MUL_13[a3]
        result[c + 8]  = _GF_MUL_13[a0] ^ _GF_MUL_9[a1]  ^ _GF_MUL_14[a2] ^ _GF_MUL_11[a3]
        result[c + 12] = _GF_MUL_11[a0] ^ _GF_MUL_13[a1] ^ _GF_MUL_9[a2]  ^ _GF_MUL_14[a3]

    return result


# ---------------------------------------------------------------------------
# Round key helpers
# ---------------------------------------------------------------------------

def transpose_round_keys(round_keys: List[bytes]) -> List[bytes]:
    """Transpose standard round keys to DLL's row-major format.

    Standard AES key schedule produces round keys in column-major order.
    The DLL expects them in row-major order. This function converts each
    round key.

    Args:
        round_keys: List of round keys (each 16 bytes) in standard
                    column-major order.

    Returns:
        List of round keys in DLL row-major order.
    """
    return [bytes(transpose(list(rk))) for rk in round_keys]


def aes_key_expand(key: bytes) -> List[bytes]:
    """Standard AES-128 key expansion.

    Derives 11 round keys (K0..K10) from a 16-byte AES key using
    the standard AES key schedule algorithm. Round keys are returned
    in standard column-major order (use transpose_round_keys to convert).

    Args:
        key: 16-byte AES key.

    Returns:
        List of 11 round keys (each 16 bytes) in column-major order.

    Raises:
        ValueError: If key is not exactly 16 bytes.
    """
    if len(key) != 16:
        raise ValueError(f"AES-128 key must be 16 bytes, got {len(key)}")

    # Standard Rcon values for AES-128 (10 rounds)
    rcon = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1B, 0x36]

    # Initialize with 4 words from the key (column-major)
    w = [0] * 44
    for i in range(4):
        w[i] = (key[4 * i] << 24) | (key[4 * i + 1] << 16) | (key[4 * i + 2] << 8) | key[4 * i + 3]

    for i in range(4, 44):
        temp = w[i - 1]
        if i % 4 == 0:
            # RotWord: [a0, a1, a2, a3] → [a1, a2, a3, a0]
            temp = ((temp << 8) | (temp >> 24)) & 0xFFFFFFFF
            # SubWord
            temp = (
                (S_BOX[(temp >> 24) & 0xFF] << 24) |
                (S_BOX[(temp >> 16) & 0xFF] << 16) |
                (S_BOX[(temp >> 8) & 0xFF] << 8) |
                S_BOX[temp & 0xFF]
            )
            # XOR Rcon
            temp ^= (rcon[(i // 4) - 1] << 24)
        w[i] = w[i - 4] ^ temp

    # Convert words to 16-byte round keys
    round_keys = []
    for r in range(11):
        rk = bytearray(16)
        for j in range(4):
            rk[j * 4] = (w[r * 4 + j] >> 24) & 0xFF
            rk[j * 4 + 1] = (w[r * 4 + j] >> 16) & 0xFF
            rk[j * 4 + 2] = (w[r * 4 + j] >> 8) & 0xFF
            rk[j * 4 + 3] = w[r * 4 + j] & 0xFF
        round_keys.append(bytes(rk))

    return round_keys


# ---------------------------------------------------------------------------
# Core AES-ECB block decrypt
# ---------------------------------------------------------------------------

def aes_ecb_decrypt_block(block: bytes, round_keys: List[bytes]) -> bytes:
    """Decrypt a single 16-byte AES-ECB block.

    Matches the implementation in aliplayerVS.dll sub_64F240.

    The algorithm:
    1. Transpose block from column-major to row-major (DLL internal format)
    2. XOR with K_round_count (last round key)
    3. For round = round_count-1 down to 0:
       a. InvShiftRows (byte rotation)
       b. InvSubBytes (inverse S-box)
       c. XOR with K_round
       d. InvMixColumns (except last round)
    4. Transpose back to column-major

    Args:
        block: 16 bytes of ciphertext in standard column-major order.
        round_keys: List of round keys (each 16 bytes) in **row-major**
                    order (DLL format). Use transpose_round_keys() to
                    convert from standard column-major round keys.

    Returns:
        16 bytes of plaintext in standard column-major order.

    Raises:
        ValueError: If block is not 16 bytes, or round_keys count is wrong.
    """
    if len(block) != 16:
        raise ValueError(f"Block must be 16 bytes, got {len(block)}")

    round_count = len(round_keys) - 1
    if round_count < 1:
        raise ValueError(f"Need at least 2 round keys, got {len(round_keys)}")

    # Step 1: Transpose to row-major
    state = transpose(list(block))

    # Step 2: XOR with last round key (K_round_count)
    for i in range(16):
        state[i] ^= round_keys[round_count][i]

    # Step 3: Main loop
    for rnd in range(round_count - 1, -1, -1):
        # a) InvShiftRows
        state = inv_shift_rows(state)
        # b) InvSubBytes
        state = inv_sub_bytes(state)
        # c) XOR round key
        for i in range(16):
            state[i] ^= round_keys[rnd][i]
        # d) InvMixColumns (skip on last round)
        if rnd > 0:
            state = inv_mix_columns(state)

    # Step 4: Transpose back to column-major
    result = transpose(state)

    return bytes(result)
