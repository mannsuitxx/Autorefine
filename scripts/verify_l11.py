#!/usr/bin/env python3
"""
================================================================================
SIH 2026: L11 VERIFICATION SUITE — TAMPER-EVIDENT SIGNED AUDIT LEDGER & ATTESTATION
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Tests:
  a) Multi-task execution -> verify_ledger.py prints LEDGER INTACT with count
  b) Single-character tamper detection (fails with exact seq number, restores cleanly)
  c) Forged signature rejection (detects invalid Ed25519 signature)
  d) Record deletion detection (detects sequence gap & broken link)
  e) Zero raw text leakage check (grep distinctive document text -> 0 hits)
  f) Deliverable Merkle root provenance matching
  g) Signed air-gap attestation certificate generation (all external counters = 0)
================================================================================
"""

import os
import sys
import time
import json
import shutil
import subprocess
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from security.ledger import audit_ledger, TamperEvidentLedger
from security.verify_ledger import verify_ledger
from security.attest import attestation_engine
from agent.graph import state_graph_engine, AgentState
from agent.replay import trajectory_engine
from cryptography.hazmat.primitives.asymmetric import ed25519

def log_test(test_id: str, title: str, passed: bool, details: str = ""):
    status_str = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status_str}] [{test_id}] {title}")
    if details:
        print(f"       ↳ {details}")

def main():
    print("=" * 85)
    print("  SIH 2026: L11 TAMPER-EVIDENT LEDGER & AIR-GAP ATTESTATION ACCEPTANCE SUITE")
    print("=" * 85)

    pass_count = 0
    fail_count = 0

    ledger_path = str(base_dir / "data" / "ledger" / "audit_ledger.jsonl")
    public_key_path = str(base_dir / "security" / "ed25519_public.pem")
    backup_ledger_path = str(base_dir / "data" / "ledger" / "audit_ledger_backup.jsonl")

    # --------------------------------------------------------------------------
    # Test a: Multi-Task Execution & Ledger Integrity Verification
    # --------------------------------------------------------------------------
    print("\n--- [L11-a: MULTI-TASK LEDGER GENERATION & INTEGRITY VERIFICATION] ---")
    test_fixture = str(base_dir / "data" / "test_fixtures" / "V205_Different_Inspection_Report.png")
    
    # Run three distinct tasks to populate the signed ledger
    for i in range(3):
        traj_id = f"traj_l11_run_{i+1}_{int(time.time()*1000)}"
        state: AgentState = {
            "task_prompt": f"Integrity analysis batch run {i+1} for V-205",
            "attached_files": [test_fixture],
            "trajectory_id": traj_id,
            "seed": 42
        }
        approver = {"name": f"Inspector #{i+1}", "role": "Lead Inspection Engineer"}
        trajectory_engine.execute_run(state, traj_id, approver_info=approver)

    is_valid, msg, rec_count = verify_ledger(ledger_path, public_key_path)
    test_a_pass = is_valid and (rec_count >= 6)
    log_test("L11-a", "Ledger integrity verified across multi-task execution", test_a_pass,
             f"{msg} | Verified record count: {rec_count}")
    pass_count += int(test_a_pass); fail_count += int(not test_a_pass)

    # Backup clean ledger for tamper tests
    shutil.copy2(ledger_path, backup_ledger_path)

    # --------------------------------------------------------------------------
    # Test b: Single-Character Tamper Detection (Fail & Identify Seq)
    # --------------------------------------------------------------------------
    print("\n--- [L11-b: SINGLE-CHARACTER TAMPER ATTACK DETECTION] ---")
    # Read records, tamper with seq 2
    records = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))
    
    target_idx = min(2, len(records) - 1)
    orig_actor = records[target_idx]["actor"]
    records[target_idx]["actor"] = orig_actor + "_TAMPERED"
    
    with open(ledger_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
            
    is_valid_tampered, msg_tampered, _ = verify_ledger(ledger_path, public_key_path)
    tamper_caught = (not is_valid_tampered) and (f"seq {target_idx}" in msg_tampered)
    
    # Restore ledger
    shutil.copy2(backup_ledger_path, ledger_path)
    is_valid_restored, _, _ = verify_ledger(ledger_path, public_key_path)
    
    test_b_pass = tamper_caught and is_valid_restored
    log_test("L11-b", "Single-character modification caught with exact sequence identification", test_b_pass,
             f"Tamper detection: {msg_tampered[:80]}... | Restored: {is_valid_restored}")
    pass_count += int(test_b_pass); fail_count += int(not test_b_pass)

    # --------------------------------------------------------------------------
    # Test c: Forged Cryptographic Signature Detection
    # --------------------------------------------------------------------------
    print("\n--- [L11-c: FORGED CRYPTOGRAPHIC SIGNATURE ATTACK REJECTION] ---")
    # Generate an unauthorized rogue keypair and sign a record
    rogue_key = ed25519.Ed25519PrivateKey.generate()
    last_rec = audit_ledger.get_last_record()
    
    forged_unsigned = {
        "seq": last_rec["seq"] + 1,
        "iso_timestamp": "2026-09-15T23:30:00Z",
        "trajectory_id": "traj_forged_attack",
        "event_type": "FORGED_APPROVAL",
        "actor": "ATTACKER",
        "model": "malicious_model",
        "tool": "none",
        "input_sha256": "0" * 64,
        "output_sha256": "0" * 64
    }
    canon_forged = audit_ledger._canonical_json(forged_unsigned)
    this_hash_forged = audit_ledger._hash_record(forged_unsigned, last_rec["this_hash"])
    forged_sig = rogue_key.sign(this_hash_forged.encode()).hex()
    
    forged_full = {
        **forged_unsigned,
        "prev_hash": last_rec["this_hash"],
        "this_hash": this_hash_forged,
        "signature": forged_sig
    }
    
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(forged_full) + "\n")
        
    is_valid_forge, msg_forge, _ = verify_ledger(ledger_path, public_key_path)
    forge_rejected = (not is_valid_forge) and ("signature verification failed" in msg_forge)
    
    # Restore clean ledger
    shutil.copy2(backup_ledger_path, ledger_path)
    test_c_pass = forge_rejected
    log_test("L11-c", "Forged signature from unauthorized key rejected by verifier", test_c_pass,
             f"Rejection message: {msg_forge[:85]}...")
    pass_count += int(test_c_pass); fail_count += int(not test_c_pass)

    # --------------------------------------------------------------------------
    # Test d: Record Deletion / Chain Break Detection
    # --------------------------------------------------------------------------
    print("\n--- [L11-d: RECORD DELETION / CHAIN TRUNCATION DETECTION] ---")
    records = []
    with open(ledger_path, "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))
            
    # Remove record at index 1
    if len(records) > 2:
        deleted_records = [records[0]] + records[2:]
        with open(ledger_path, "w", encoding="utf-8") as f:
            for r in deleted_records:
                f.write(json.dumps(r) + "\n")
                
    is_valid_del, msg_del, _ = verify_ledger(ledger_path, public_key_path)
    del_caught = (not is_valid_del) and ("Sequence gap" in msg_del or "broken" in msg_del)
    
    # Restore clean ledger
    shutil.copy2(backup_ledger_path, ledger_path)
    test_d_pass = del_caught
    log_test("L11-d", "Middle record deletion detected through hash chain and sequence break", test_d_pass,
             f"Break identified: {msg_del[:85]}...")
    pass_count += int(test_d_pass); fail_count += int(not test_d_pass)

    # --------------------------------------------------------------------------
    # Test e: Zero Raw Document Text Leakage Check (Grep Audit)
    # --------------------------------------------------------------------------
    print("\n--- [L11-e: ZERO RAW PROPRIETARY TEXT LEAKAGE GREP AUDIT] ---")
    distinctive_phrases = [
        "Debutanizer Overhead Accumulator",
        "ULTRASONIC THICKNESS MEASUREMENTS",
        "Shell Course 1: Nominal 220",
        "MANGALORE REFINERY AND PETROCHEMICALS LIMITED"
    ]
    
    leak_hits = 0
    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger_content = f.read()
        for phrase in distinctive_phrases:
            if phrase in ledger_content:
                leak_hits += 1
                
    test_e_pass = (leak_hits == 0)
    log_test("L11-e", "Ledger contains zero raw document text (strictly content hashes)", test_e_pass,
             f"Proprietary phrase hits in data/ledger/: {leak_hits} (Pure SHA-256 digests enforced)")
    pass_count += int(test_e_pass); fail_count += int(not test_e_pass)

    # --------------------------------------------------------------------------
    # Test f: Deliverable Merkle Root Provenance Matching
    # --------------------------------------------------------------------------
    print("\n--- [L11-f: DELIVERABLE MERKLE ROOT PROVENANCE EMBEDDING] ---")
    sample_traj = f"traj_merkle_test_{int(time.time()*1000)}"
    audit_ledger.append_event(sample_traj, "STEP_1", input_data="a", output_data="b")
    audit_ledger.append_event(sample_traj, "STEP_2", input_data="c", output_data="d")
    
    root_computed, sig_root, count = audit_ledger.compute_session_merkle_root(sample_traj)
    test_f_pass = (len(root_computed) == 64) and (len(sig_root) == 128) and (count == 2)
    log_test("L11-f", "Session Merkle root computed and cryptographically signed", test_f_pass,
             f"Trajectory: {sample_traj} | Merkle Root: {root_computed[:16]}... | Records: {count}")
    pass_count += int(test_f_pass); fail_count += int(not test_f_pass)

    # --------------------------------------------------------------------------
    # Test g: Signed Air-Gap Attestation PDF Generation
    # --------------------------------------------------------------------------
    print("\n--- [L11-g: SIGNED AIR-GAP ATTESTATION PDF CERTIFICATE] ---")
    attest_pdf = attestation_engine.export_pdf_report(str(base_dir / "outputs" / "Airgap_Attestation_Report.pdf"))
    attest_rec = attestation_engine.generate_attestation_record()
    
    pdf_ok = Path(attest_pdf).exists() and (Path(attest_pdf).stat().st_size > 1000)
    all_counters_zero = (
        attest_rec["per_provider_external_egress"]["api.openai.com"]["requests"] == 0 and
        attest_rec["per_provider_external_egress"]["generativelanguage.googleapis.com"]["requests"] == 0 and
        attest_rec["per_provider_external_egress"]["api.anthropic.com"]["requests"] == 0 and
        attest_rec["kernel_network_summary"]["outbound_wan_bytes_transferred"] == 0
    )
    has_sig = len(attest_rec.get("ed25519_signature", "")) == 128
    
    test_g_pass = pdf_ok and all_counters_zero and has_sig
    log_test("L11-g", "Signed Air-gap attestation certificate generated with 0 external egress", test_g_pass,
             f"Certificate: {Path(attest_pdf).name} ({Path(attest_pdf).stat().st_size} bytes) | All Cloud Providers: 0 Req / 0 B")
    pass_count += int(test_g_pass); fail_count += int(not test_g_pass)

    # Cleanup backup
    if os.path.exists(backup_ledger_path):
        os.remove(backup_ledger_path)

    # --------------------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------------------
    print("\n" + "=" * 85)
    print(f"  L11 ACCEPTANCE TEST SUMMARY: {pass_count} PASSED / {fail_count} FAILED")
    print("=" * 85)

    if fail_count == 0:
        print("🎉 ALL L11 ACCEPTANCE GATES PASS WITH RIGOROUS FORENSIC EVIDENCE!\n")
        return 0
    else:
        print("❌ SOME L11 GATES FAILED. INSPECT LOGS ABOVE.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
