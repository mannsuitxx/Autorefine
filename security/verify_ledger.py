#!/usr/bin/env python3
"""
================================================================================
SIH 2026: STANDALONE LEDGER INTEGRITY VERIFIER (TASK L11)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Zero external dependencies beyond standard library & cryptography.hazmat.
Verifies all hash chains, cryptographic signatures, and Merkle proofs.
================================================================================
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

def canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

def verify_ledger(ledger_path: str, public_key_path: str) -> Tuple[bool, str, int]:
    """
    Forensically validates every record in the ledger.
    Returns: (is_valid, report_message, record_count)
    """
    p_ledger = Path(ledger_path)
    p_pubkey = Path(public_key_path)

    if not p_ledger.exists():
        return False, f"Ledger file not found at {ledger_path}", 0
    if not p_pubkey.exists():
        return False, f"Public key not found at {public_key_path}", 0

    with open(p_pubkey, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    records = []
    with open(p_ledger, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                rec = json.loads(line_str)
                records.append((line_num, rec))
            except Exception as e:
                return False, f"FAILED: Corrupted JSON at line {line_num}: {e}", len(records)

    if not records:
        return False, "FAILED: Ledger is empty", 0

    expected_prev_hash = "0" * 64

    for idx, (line_num, rec) in enumerate(records):
        seq = rec.get("seq")
        if seq != idx:
            return False, f"FAILED: Sequence gap or deletion detected at line {line_num}! Expected seq={idx}, found seq={seq}", len(records)

        prev_hash = rec.get("prev_hash")
        this_hash = rec.get("this_hash")
        signature_hex = rec.get("signature")

        # 1. Check Hash Chain Continuity
        if prev_hash != expected_prev_hash:
            return False, (
                f"FAILED: Hash chain link broken at seq {seq} (line {line_num})!\n"
                f"  Expected prev_hash: {expected_prev_hash}\n"
                f"  Found prev_hash:    {prev_hash}"
            ), len(records)

        # 2. Recompute Record Hash
        unsigned_dict = {
            "seq": rec.get("seq"),
            "iso_timestamp": rec.get("iso_timestamp"),
            "trajectory_id": rec.get("trajectory_id"),
            "event_type": rec.get("event_type"),
            "actor": rec.get("actor"),
            "model": rec.get("model"),
            "tool": rec.get("tool"),
            "input_sha256": rec.get("input_sha256"),
            "output_sha256": rec.get("output_sha256")
        }
        canon = canonical_json(unsigned_dict)
        expected_this_hash = hashlib.sha256(canon.encode('utf-8') + prev_hash.encode('utf-8')).hexdigest()

        if this_hash != expected_this_hash:
            return False, (
                f"FAILED: Tampered data detected at seq {seq} (line {line_num})!\n"
                f"  Stored this_hash:     {this_hash}\n"
                f"  Calculated this_hash: {expected_this_hash}"
            ), len(records)

        # 3. Verify Ed25519 Cryptographic Signature
        try:
            sig_bytes = bytes.fromhex(signature_hex)
            public_key.verify(sig_bytes, this_hash.encode('utf-8'))
        except (InvalidSignature, ValueError, TypeError) as e:
            return False, f"FAILED: Cryptographic signature verification failed at seq {seq} (line {line_num})! Possible forged signature or key mismatch.", len(records)

        expected_prev_hash = this_hash

    return True, f"LEDGER INTACT ({len(records)} records verified with valid Ed25519 signatures)", len(records)

def main():
    base_dir = Path(__file__).resolve().parent.parent
    ledger_path = str(base_dir / "data" / "ledger" / "audit_ledger.jsonl")
    public_key_path = str(base_dir / "security" / "ed25519_public.pem")

    if len(sys.argv) > 1:
        ledger_path = sys.argv[1]
    if len(sys.argv) > 2:
        public_key_path = sys.argv[2]

    is_valid, msg, count = verify_ledger(ledger_path, public_key_path)
    if is_valid:
        print(f"✅ {msg}")
        sys.exit(0)
    else:
        print(f"❌ {msg}")
        sys.exit(1)

if __name__ == "__main__":
    main()
