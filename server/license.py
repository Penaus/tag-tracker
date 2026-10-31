"""Offline license verification (no server needed).

A license key is `payload.signature`, both base64url:
  payload  = JSON {"d": device_id or "*", "t": max_tags, "e": expiry_epoch or 0}
  signature= Ed25519 signature of payload, made by the SELLER's private key.

The app embeds only the PUBLIC key, so it can verify a key but never forge one.
Keys are device-bound: a key made for one phone won't unlock another.
"""
import base64
import json
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Public key of the license signer. The matching PRIVATE key lives only in the
# separate key-generator app (private repo) — never here.
PUBLIC_KEY_HEX = "fbf4124b4c0cd6faeb1b2ea9960a48f69b4cf14649aea404142df8cec0cef96b"

FREE_TAGS = 1
FREE_HISTORY_HOURS = 24


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def verify(key: str, device_id: str, activated_ts: int = 0) -> dict:
    """Returns {'licensed','tags','expiry','dur','reason'}.
    Expiry can be absolute ("e") or a DURATION in days from activation ("dur").
    For "dur" keys, pass activated_ts (when the buyer first entered the key); the clock
    starts then, so "7 days" = 7 days from activation, not from generation."""
    try:
        payload_b64, sig_b64 = key.strip().split(".")
        payload = _b64d(payload_b64)
        sig = _b64d(sig_b64)
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX)).verify(sig, payload)
        data = json.loads(payload)
    except (ValueError, InvalidSignature, Exception):
        return {"licensed": False, "tags": FREE_TAGS, "dur": 0, "reason": "Invalid or corrupted key"}
    if data.get("d") not in ("*", device_id):
        return {"licensed": False, "tags": FREE_TAGS, "dur": 0, "reason": "This key belongs to a different phone"}
    now = int(time.time())
    exp = int(data.get("e", 0) or 0)          # absolute expiry epoch (0 = none)
    dur = int(data.get("dur", 0) or 0)        # days-from-activation (0 = none)
    if dur and activated_ts:
        exp_from_activation = int(activated_ts) + dur * 86400
        exp = exp_from_activation if not exp else min(exp, exp_from_activation)
    if exp and now > exp:
        return {"licensed": False, "tags": FREE_TAGS, "dur": dur, "reason": "Key expired"}
    return {"licensed": True, "tags": int(data.get("t", 1)), "expiry": exp, "dur": dur, "reason": ""}
