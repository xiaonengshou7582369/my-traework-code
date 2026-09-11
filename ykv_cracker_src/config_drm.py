# Copyright (C) 2026 RainVenturer
# SPDX-License-Identifier: GPL-3.0
"""ConfigContextDrm (sub_18021B700) — YKV decryption configuration entry point.

Wires together the already-implemented decryption primitives:

    key_unwrap()  (key_unwrap.py)     — 3-layer AES key unwrapping
    custom_b64_decode() (custom_b64.py) — custom base64 decode
    aes_key_expand()  (aes_core.py)   — AES-128 key expansion to round keys

The implementation mirrors aliplayerVS.dll's ConfigContextDrm function
(sub_18021B700), which:

    1. Checks a drm_type bitmask (only 2, 8, 16, 32 pass)
    2. Unwraps the 3-part comma-separated key string
       (key_unwrap, sub_180256020)
    3. Runs the first 24 bytes of the decrypted payload through
       custom base64 decoding (sub_18064EDD0) to produce 18 bytes
       of key material
    4. Uses the first 16 bytes of key material as the AES-128 key
       for aes_key_expand (sub_18064EBD0)

    For the playback path (drm_type=2, flag=0), this follows the
    non-CMAF branch through tbEncryptionInit (sub_18064EF70).
"""

from __future__ import annotations

import base64
import hashlib

from Crypto.Cipher import AES

from ykv_cracker.aes_core import aes_key_expand
from ykv_cracker.custom_b64 import custom_b64_decode
from ykv_cracker.key_unwrap import _md5_hex_key, _strlen

# ---------------------------------------------------------------------------
# Bitmask gate matching _bittest64(&0x100010104LL, drm_type)
#
# 0x100010104 in binary has bits 2, 8, 16, 32 set:
#   0x100010104 = 1_0000_0000_0000_0001_0000_0001_0000_0100
#                  ^bit32      ^bit16     ^bit8      ^bit2
#
# Only drm_type values 2, 8, 16, 32 pass the gate.
# ---------------------------------------------------------------------------
_DRM_TYPE_BITMASK = 0x100010104


def check_drm_type(drm_type: int) -> bool:
    """Check drm_type against the bitmask gate.

    Matches the DLL's _bittest64(&0x100010104LL, drm_type) check at
    sub_18021B700+0x4D (address 0x21B7ED).

    Args:
        drm_type: DRM type value to validate.

    Returns:
        True if drm_type is 2, 8, 16, or 32. False otherwise.
    """
    if drm_type < 0 or drm_type > 63:
        return False
    return bool(_DRM_TYPE_BITMASK & (1 << drm_type))


def _unwrap_full(key_string: str) -> bytes:
    """Perform the full 2-layer AES key unwrap, returning ALL decrypted part3 data.

    This is equivalent to sub_180256020's full output (the 96-byte Src buffer
    that gets memcpy'd to the caller's v21 buffer), limited to the actual
    decrypted payload (32 bytes = 2 AES-ECB blocks of the base64-decoded part3).

    Args:
        key_string: Comma-separated 3-part key string
                    "id,part2_b64,part3_b64" as received from the DRM server.

    Returns:
        32 bytes of decrypted part3 data.

    Raises:
        ValueError: If key_string format is invalid.
    """
    parts = key_string.split(",")
    if len(parts) != 3:
        raise ValueError(
            f"Expected 3 comma-separated parts, got {len(parts)}"
        )

    part1, part2_b64, part3_b64 = [p.strip() for p in parts]

    if not part1 or not part2_b64 or not part3_b64:
        raise ValueError("All three key parts must be non-empty")

    # -- Layer 1: Decrypt part2 to recover R2 --
    # MD5(part1)[4:12] -> hex -> 16-byte ASCII key K1
    k1 = _md5_hex_key(part1.encode("ascii"))

    # Standard-base64-decode part2
    data2 = base64.b64decode(part2_b64)

    # AES-ECB decrypt first block
    cipher1 = AES.new(k1, AES.MODE_ECB)
    r2_block = cipher1.decrypt(data2[:16])

    # Extract null-terminated R2 string
    r2_len = _strlen(r2_block)
    r2 = r2_block[:r2_len] if r2_len > 0 else b""

    # -- Layer 2: Decrypt part3 to get full payload --
    # MD5(part1 + R2)[4:12] -> hex -> 16-byte ASCII key K2
    #   (DLL sub_CF480 appends R2 to the part1 buffer, so MD5 gets
    #    part1 || R2, not R2 alone)
    k2 = _md5_hex_key(part1.encode("ascii") + r2)

    # Standard-base64-decode part3
    data3 = base64.b64decode(part3_b64)

    # AES-ECB decrypt all blocks
    cipher2 = AES.new(k2, AES.MODE_ECB)
    return cipher2.decrypt(data3)


def setup_decryption(
    drm_type: int,
    key_string: str,
    flag: int = 0,
) -> list:
    """Configure YKV decryption and return AES round keys.

    This is the Python equivalent of ConfigContextDrm (sub_18021B700)
    in aliplayerVS.dll.  For the playback path (drm_type=2, flag=0),
    the function:

    1. Checks drm_type against the bitmask gate.
    2. Unwraps the 3-part key string via _unwrap_full (sub_180256020).
    3. Decodes the first 24 bytes of decrypted payload through
       custom_b64_decode (sub_18064EDD0) to produce 18 bytes of
       key material.
    4. Uses the first 16 bytes of key material as an AES-128 key
       and expands it via aes_key_expand (sub_18064EBD0).

    Args:
        drm_type: DRM type.  Pass 2 for standard playback.
        key_string: 3-part comma-separated key string.
        flag: 0 = non-CMAF (playback path, the only path implemented
              here).  Non-zero would be the CMAF path through
              tbEncryptionInit.

    Returns:
        List of 11 round keys (each 16 bytes) in standard column-major
        order, suitable for passing to aes_ecb_decrypt_block after
        transpose_round_keys.

    Raises:
        ValueError: If drm_type is not valid, key_string is malformed,
                    or processing fails.
    """
    if not check_drm_type(drm_type):
        raise ValueError(
            f"Unsupported drm_type {drm_type}: must be 2, 8, 16, or 32"
        )

    if "," not in key_string:
        raise ValueError(
            "key_string must be in format 'id,part2_b64,part3_b64'"
        )

    # Step 1: Full key unwrap -> complete decrypted part3 payload
    full_payload = _unwrap_full(key_string)

    # Step 2: custom_b64_decode on first 24 bytes -> 18 bytes key material
    # This mirrors the DLL: sub_64EDD0(v20, v21, strlen(v21)) where v21
    # contains the full decrypted part3 output from sub_256020.
    key_material = custom_b64_decode(full_payload[:24])

    # Step 3: AES-128 key expansion on first 16 bytes of key material
    # This mirrors sub_64EBD0 called from tbEncryptionInit in non-CMAF mode.
    round_keys = aes_key_expand(key_material[:16])

    return round_keys
