# Copyright (C) 2026 RainVenturer
# SPDX-License-Identifier: GPL-3.0
"""Custom base64 decoder (sub_18064EDD0 in aliplayerVS.dll).

Decodes 24 bytes of custom-base64-encoded data into 18 bytes of binary output
using a non-standard base64 alphabet that excludes 'A'.

The decode table is built inline on the stack in the original DLL. This Python
implementation reconstructs the same table and applies the same bit-packing
logic.
"""

from __future__ import annotations

# Maximum valid input length
CUSTOM_B64_INPUT_SIZE = 24
CUSTOM_B64_OUTPUT_SIZE = 18


def _build_decode_table() -> bytearray:
    """Build the 256-byte decode lookup table matching sub_18064EDD0.

    The table maps each input byte value (0-255) to its decoded 6-bit value.
    Entries not explicitly set default to 0 (matching the memset behavior).

    Custom alphabet (no 'A'):
        B-Z  ->  1-25
        a-z  -> 26-51
        0-9  -> 52-61
        +    -> 62
        /    -> 63
    """
    table = bytearray(256)  # All zeros

    # '+' (0x2B) -> 62,  '/' (0x2F) -> 63
    table[0x2B] = 62
    table[0x2F] = 63

    # '0' (0x30) through '9' (0x39) -> 52-61
    for i in range(10):
        table[0x30 + i] = 52 + i

    # 'B' (0x42) through 'Z' (0x5A) -> 1-25
    for i in range(25):
        table[0x42 + i] = 1 + i

    # 'a' (0x61) through 'z' (0x7A) -> 26-51
    for i in range(26):
        table[0x61 + i] = 26 + i

    return table


# Pre-built decode table (constructed once at module load)
_DECODE_TABLE = _build_decode_table()


def custom_b64_decode(data: bytes) -> bytes:
    """Custom base64 decode, 24 bytes -> 18 bytes.

    Matches aliplayerVS.dll sub_18064EDD0.

    The function:
    1. Translates each input byte through the decode table (6-bit lookup).
    2. Packs the 24 6-bit values (144 bits) into 18 bytes of output.

    Args:
        data: Exactly 24 bytes of custom-base64-encoded data.

    Returns:
        18 bytes of decoded binary output.

    Raises:
        ValueError: If input is not exactly 24 bytes.
    """
    if len(data) != CUSTOM_B64_INPUT_SIZE:
        raise ValueError(
            f"Input must be exactly {CUSTOM_B64_INPUT_SIZE} bytes, "
            f"got {len(data)}"
        )

    # Step 1: Translate each input byte through the decode table
    decoded = bytearray(CUSTOM_B64_INPUT_SIZE)
    for i, b in enumerate(data):
        decoded[i] = _DECODE_TABLE[b]

    # Step 2: Pack 6-bit values into 8-bit bytes
    output = bytearray(CUSTOM_B64_OUTPUT_SIZE)
    out_idx = 0

    # Group 4 input 6-bit values into 3 output bytes (standard base64 packing)
    for i in range(0, CUSTOM_B64_INPUT_SIZE, 4):
        a, b, c, d = decoded[i], decoded[i + 1], decoded[i + 2], decoded[i + 3]

        # First byte: high 6 bits from a, low 2 bits from b
        output[out_idx] = (a << 2) | (b >> 4)
        # Second byte: high 4 bits from b, low 4 bits from c
        output[out_idx + 1] = ((b & 0x0F) << 4) | (c >> 2)
        # Third byte: high 2 bits from c, low 6 bits from d
        output[out_idx + 2] = ((c & 0x03) << 6) | d

        out_idx += 3

    return bytes(output)


def custom_b64_encode(data: bytes) -> bytes:
    """Custom base64 encode, 18 bytes -> 24 bytes.

    Inverse of custom_b64_decode. Encodes 18 binary bytes into 24 bytes
    using the custom alphabet (B-Z, a-z, 0-9, +, /).

    Note: This is NOT the standard base64 alphabet. The character 'A' is
    excluded from the alphabet, so value 0 has no direct representation.
    For completeness, this encoder maps value 0 to... a non-deterministic
    fallback ('/' value), since the decoder treats any non-alphabet char
    as 0.

    Args:
        data: Exactly 18 bytes of binary data.

    Returns:
        24 bytes of custom-base64-encoded data.

    Raises:
        ValueError: If input is not exactly 18 bytes.
    """
    if len(data) != CUSTOM_B64_OUTPUT_SIZE:
        raise ValueError(
            f"Input must be exactly {CUSTOM_B64_OUTPUT_SIZE} bytes, "
            f"got {len(data)}"
        )

    # Build the forward alphabet (value -> character)
    alphabet = {}

    # Values 1-25 -> 'B'-'Z'
    for i in range(25):
        alphabet[1 + i] = chr(ord('B') + i)

    # Values 26-51 -> 'a'-'z'
    for i in range(26):
        alphabet[26 + i] = chr(ord('a') + i)

    # Values 52-61 -> '0'-'9'
    for i in range(10):
        alphabet[52 + i] = chr(ord('0') + i)

    # Value 62 -> '+', Value 63 -> '/'
    alphabet[62] = '+'
    alphabet[63] = '/'

    # Value 0: no valid character in this alphabet
    # Must use a character that decodes to 0 (any non-alphabet char)
    # We use 0x00 (null byte) since it decodes to 0
    alphabet[0] = '\x00'

    output = bytearray(CUSTOM_B64_INPUT_SIZE)
    out_idx = 0

    # Group 3 output bytes into 4 6-bit values
    for i in range(0, CUSTOM_B64_OUTPUT_SIZE, 3):
        a, b, c = data[i], data[i + 1], data[i + 2] if i + 1 < CUSTOM_B64_OUTPUT_SIZE else 0, data[i + 2] if i + 2 < CUSTOM_B64_OUTPUT_SIZE else 0
        a, b, c = data[i], data[i + 1], data[i + 2]

        # Extract 4 6-bit values
        val0 = a >> 2
        val1 = ((a & 0x03) << 4) | (b >> 4)
        val2 = ((b & 0x0F) << 2) | (c >> 6)
        val3 = c & 0x3F

        output[out_idx] = ord(alphabet.get(val0, '\x00'))
        output[out_idx + 1] = ord(alphabet.get(val1, '\x00'))
        output[out_idx + 2] = ord(alphabet.get(val2, '\x00'))
        output[out_idx + 3] = ord(alphabet.get(val3, '\x00'))

        out_idx += 4

    return bytes(output)
