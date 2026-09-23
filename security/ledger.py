#!/usr/bin/env python3
"""
================================================================================
SIH 2026: CRYPTOGRAPHICALLY SIGNED TAMPER-EVIDENT AUDIT LEDGER (TASK L11)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Append-only hash-chained Ed25519 ledger with Merkle tree session roots.
================================================================================
"""

import os
import sys
import time
import json
import stat
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

class TamperEvidentLedger:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent
        self.ledger_dir = self.base_dir / "data" / "ledger"
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_file = self.ledger_dir / "audit_ledger.jsonl"
        
        self.sec_dir = self.base_dir / "data" / "security"
        self.sec_dir.mkdir(parents=True, exist_ok=True)
        self.priv_key_path = self.sec_dir / "ed25519_private.key"
        self.pub_key_path = self.base_dir / "security" / "ed25519_public.pem"
        self.pub_key_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_keys()
        self._ensure_genesis()

    def _init_keys(self):
        """Initializes or loads the Ed25519 keypair, enforcing 0600 on private key."""
        if not self.priv_key_path.exists():
            private_key = ed25519.Ed25519PrivateKey.generate()
            # Save private key with 0600 permissions
            with open(self.priv_key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            os.chmod(self.priv_key_path, stat.S_IRUSR | stat.S_IWUSR)
            
            # Save public key
            public_key = private_key.public_key()
            with open(self.pub_key_path, "wb") as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
        else:
            with open(self.priv_key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)
            public_key = private_key.public_key()
            if not self.pub_key_path.exists():
                with open(self.pub_key_path, "wb") as f:
                    f.write(public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ))

        self.private_key = private_key
        self.public_key = public_key

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        """Produces deterministic canonical JSON representation."""
        return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True)

    def _hash_record(self, unsigned_dict: Dict[str, Any], prev_hash: str) -> str:
        """Computes SHA-256(canonical_json(record) + prev_hash)."""
        canon = self._canonical_json(unsigned_dict)
        payload = canon.encode('utf-8') + prev_hash.encode('utf-8')
        return hashlib.sha256(payload).hexdigest()

    def _sign_hash(self, hash_hex: str) -> str:
        """Signs the hash hex string using Ed25519 private key."""
        sig_bytes = self.private_key.sign(hash_hex.encode('utf-8'))
        return sig_bytes.hex()

    def get_last_record(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent ledger record if file exists and is not empty."""
        if not self.ledger_file.exists():
            return None
        last_line = None
        with open(self.ledger_file, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    last_line = line_str
        if last_line:
            return json.loads(last_line)
        return None

    def _ensure_genesis(self):
        """Creates the genesis block if the ledger is empty."""
        if not self.ledger_file.exists() or self.ledger_file.stat().st_size == 0:
            genesis_payload = {
                "seq": 0,
                "iso_timestamp": datetime.now(timezone.utc).isoformat(),
                "trajectory_id": "traj_genesis_00000000",
                "event_type": "GENESIS",
                "actor": "MRPL_SOVEREIGN_SYSTEM",
                "model": "SYSTEM_CORE",
                "tool": "TamperEvidentLedger._ensure_genesis",
                "input_sha256": hashlib.sha256(b"MRPL_GENESIS_SEED").hexdigest(),
                "output_sha256": hashlib.sha256(b"INITIALIZED_AIRGAP_LEDGER").hexdigest(),
            }
            prev_hash = "0" * 64
            this_hash = self._hash_record(genesis_payload, prev_hash)
            sig_hex = self._sign_hash(this_hash)
            
            genesis_record = {
                **genesis_payload,
                "prev_hash": prev_hash,
                "this_hash": this_hash,
                "signature": sig_hex
            }
            
            with open(self.ledger_file, "w", encoding="utf-8") as f:
                f.write(json.dumps(genesis_record) + "\n")

    def append_event(
        self,
        trajectory_id: str,
        event_type: str,
        actor: str = "Agent",
        model: str = "qwen2.5:1.5b",
        tool: str = "StateGraph",
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Appends a cryptographically signed, hash-chained record containing ONLY content hashes.
        Never writes raw proprietary document text to the ledger.
        """
        last_rec = self.get_last_record()
        if last_rec:
            seq = last_rec["seq"] + 1
            prev_hash = last_rec["this_hash"]
        else:
            seq = 0
            prev_hash = "0" * 64

        # Compute content hashes
        input_sha = hashlib.sha256(self._canonical_json({"data": input_data}).encode('utf-8')).hexdigest()
        output_sha = hashlib.sha256(self._canonical_json({"data": output_data}).encode('utf-8')).hexdigest()

        record_unsigned = {
            "seq": seq,
            "iso_timestamp": datetime.now(timezone.utc).isoformat(),
            "trajectory_id": str(trajectory_id),
            "event_type": str(event_type),
            "actor": str(actor),
            "model": str(model),
            "tool": str(tool),
            "input_sha256": input_sha,
            "output_sha256": output_sha,
        }

        this_hash = self._hash_record(record_unsigned, prev_hash)
        signature_hex = self._sign_hash(this_hash)

        full_record = {
            **record_unsigned,
            "prev_hash": prev_hash,
            "this_hash": this_hash,
            "signature": signature_hex
        }

        with open(self.ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(full_record) + "\n")

        return full_record

    def compute_session_merkle_root(self, trajectory_id: str) -> Tuple[str, str, int]:
        """
        Computes the Merkle root of all record hashes belonging to a given trajectory/session.
        Returns: (merkle_root_hex, signature_hex, record_count)
        """
        session_hashes = []
        if self.ledger_file.exists():
            with open(self.ledger_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        rec = json.loads(line_str)
                        if rec.get("trajectory_id") == trajectory_id:
                            session_hashes.append(rec["this_hash"])

        if not session_hashes:
            # Fallback to hash of empty session
            leaf = hashlib.sha256(trajectory_id.encode('utf-8')).hexdigest()
            session_hashes = [leaf]

        # Tree reduction
        current_layer = list(session_hashes)
        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                h1 = current_layer[i]
                h2 = current_layer[i + 1] if (i + 1) < len(current_layer) else h1
                comb = hashlib.sha256((h1 + h2).encode('utf-8')).hexdigest()
                next_layer.append(comb)
            current_layer = next_layer

        merkle_root = current_layer[0]
        sig_hex = self._sign_hash(merkle_root)
        return (merkle_root, sig_hex, len(session_hashes))

    def get_all_records(self) -> List[Dict[str, Any]]:
        """Returns all records in the ledger."""
        records = []
        if self.ledger_file.exists():
            with open(self.ledger_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if line_str:
                        records.append(json.loads(line_str))
        return records

    def get_recent_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns up to `limit` most recent records."""
        all_recs = self.get_all_records()
        return all_recs[-limit:]

# Global Ledger Instance
audit_ledger = TamperEvidentLedger()

if __name__ == "__main__":
    rec = audit_ledger.append_event(
        trajectory_id="traj_demo_001",
        event_type="TEST_EVENT",
        actor="CLI",
        model="system",
        tool="main",
        input_data={"test": 123},
        output_data={"status": "OK"}
    )
    print(f"Appended ledger record seq={rec['seq']}, this_hash={rec['this_hash']}")
    root, sig, count = audit_ledger.compute_session_merkle_root("traj_demo_001")
    print(f"Merkle Root: {root} (Signature: {sig[:16]}...) across {count} records")
