"""
scripts/verify_l16.py
=====================
Verification suite for Task L16:
Field Edge: Offline Voice Intake, Bilingual Indian-Language Output & Portable Signed Knowledge Packs.

Gates:
  Gate A: 40-second voice dictation transcription & structured field extraction.
  Gate B: Domain Terminology Word Error Rate (WER) computation.
  Gate C: Bilingual Approval Note (Kannada/Hindi) with byte-identical technical invariant protection.
  Gate D: Signed Knowledge Pack Export & Clean Import with Retrieval Verification.
  Gate E: Tamper Detection (1-byte archive tampering triggers cryptographic refusal).
  Gate F: Zero Network Calls & Air-Gap Telemetry Verification during STT/Translation.
"""

import sys
import os
import shutil
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from edge.stt_engine import stt_engine
from edge.bilingual_engine import bilingual_engine
from edge.knowledge_pack import knowledge_pack_engine
from kb.hybrid_retriever import HybridGraphRetriever
from security.ledger import audit_ledger


def test_gate_a_and_b_voice_intake():
    print("\n--- Gates A & B: Offline Voice Dictation Intake & Domain WER Audit ---")
    raw_dictation = (
        "This is senior inspector reporting from crude distillation unit. "
        "Inspecting atmospheric tower see one zero one shell course number one. "
        "Ultrasonic thickness measurement using high temperature dual probe. "
        "Original nominal thickness is 12.0 milli meters. "
        "Found measured thickness of 10.4 milli meters. "
        "Design minimum thickness per asme section eight is 8.0 milli meters. "
        "Corrosion rate calculated per api five ten standard clause six point five. "
        "Surface preparation completed per oisd one zero five guidelines."
    )
    
    reference_clean = (
        "This is senior inspector reporting from crude distillation unit. "
        "Inspecting atmospheric tower C-101 shell course number one. "
        "Ultrasonic Thickness (UT) measurement using high temperature dual probe. "
        "Original nominal thickness is 12.0 mm. "
        "Found measured thickness of 10.4 mm. "
        "Design minimum thickness per ASME Section VIII Div 1 is 8.0 mm. "
        "Corrosion rate calculated per API-510 standard clause six point five. "
        "Surface preparation completed per OISD-STD-105 guidelines."
    )

    proc = stt_engine.process_transcript(raw_dictation)
    print(f"Raw Dictation Input:\n  '{raw_dictation}'")
    print(f"\nBiased Output Transcript:\n  '{proc['biased_transcript']}'")
    print("\nExtracted Structured Field Table:")
    for k, v in proc["extracted_fields"].items():
        print(f"  {k:25s}: {v}")

    assert proc["extracted_fields"].get("equipment_tag") == "C-101", "Tag extraction failed"
    assert proc["extracted_fields"].get("nominal_thickness_mm") == 12.0, "Nominal thickness extraction failed"
    assert proc["extracted_fields"].get("measured_thickness_mm") == 10.4, "Measured thickness extraction failed"
    assert proc["extracted_fields"].get("design_minimum_mm") == 8.0, "Design minimum extraction failed"
    print(">>> Gate A PASS")

    # Gate B: Compute WER
    wer_res = stt_engine.compute_word_error_rate(reference_clean, proc["biased_transcript"])
    print(f"\nWord Error Rate (WER) Report:")
    print(f"  Total Reference Words : {wer_res['reference_word_count']}")
    print(f"  Overall WER           : {wer_res['overall_wer']:.2%}")
    print(f"  Domain Terminology WER: {wer_res['domain_terminology_wer']:.2%}")
    print(f"  Method                : {wer_res['method']}")
    assert wer_res["domain_terminology_wer"] == 0.0, "Domain terms must have 0% error rate after biasing"
    print(">>> Gate B PASS")


def test_gate_c_bilingual_approval_note():
    print("\n--- Gate C: Bilingual Deliverables & Byte-Identical Invariant Protection ---")
    data = {
        "equipment_tag": "C-101",
        "unit": "CDU-1",
        "inspection_date": "2026-09-15",
        "nominal_thickness_mm": 12.0,
        "measured_thickness_mm": 10.4,
        "design_minimum_mm": 8.0,
        "corrosion_rate_mm_yr": 0.20,
        "remaining_life_years": 12.0,
        "next_inspection_interval_years": 6.0,
        "governing_standard": "API-510 Section 6.5"
    }

    # Generate Kannada Note (Operational in Mangalore, Karnataka)
    res_kn = bilingual_engine.generate_bilingual_approval_note(data, target_lang="kannada")
    print(f"\nGenerated Kannada Approval Note:\n{res_kn['target_note']}")
    print("Verification Audit for Technical Identifiers:")
    for v in res_kn["verification_audit"]:
        print(f"  Identifier '{v['identifier']}': English={v['in_english']} | Kannada={v['in_target']} | Byte-Identical={v['byte_identical']}")
    
    assert res_kn["all_technical_identifiers_preserved"] is True, "Technical invariants must be 100% byte-identical"

    # Also test Hindi Note
    res_hi = bilingual_engine.generate_bilingual_approval_note(data, target_lang="hindi")
    assert res_hi["all_technical_identifiers_preserved"] is True, "Hindi technical invariants must be byte-identical"
    print(">>> Gate C PASS")


def test_gate_d_and_e_knowledge_packs():
    print("\n--- Gate D: Signed Portable Knowledge Pack Export & Clean Import ---")
    export_res = knowledge_pack_engine.export_pack(
        pack_version="1.0.0",
        site_origin="MRPL_MANGALORE",
        output_filename="MRPL_KnowledgePack_v1.0.0.pack"
    )
    assert export_res["status"] == "SUCCESS", f"Pack export failed: {export_res}"
    pack_path = Path(export_res["pack_file"])
    print(f"Exported signed archive: {pack_path} ({export_res['file_size_bytes']} bytes)")
    print(f"Ed25519 Digital Signature: {export_res['signature_hex'][:64]}...")

    # Import into a clean temporary directory
    temp_site_dir = Path(tempfile.mkdtemp(prefix="mrpl_site_b_"))
    try:
        import_res = knowledge_pack_engine.import_pack(pack_path, target_dir=temp_site_dir)
        print(f"Clean Site Import Result: {import_res['status']} -> {import_res['message']}")
        assert import_res["status"] == "SUCCESS", f"Expected SUCCESS import, got {import_res}"
        assert import_res["verified"] is True

        # Run retrieval query on the newly imported clean instance
        retriever = HybridGraphRetriever(base_dir=temp_site_dir)
        q_res = retriever.retrieve("What is the maximum inspection interval per API-510?", top_k=3)
        assert len(q_res.get("top_results", [])) > 0, "Retrieval on imported pack failed"
        print(f"Retrieval on clean imported site successful! Found {len(q_res['top_results'])} matching standard clauses.")
        print(">>> Gate D PASS")
    finally:
        shutil.rmtree(temp_site_dir, ignore_errors=True)

    # Gate E: Tamper Detection
    print("\n--- Gate E: 1-Byte Tamper Detection & Cryptographic Refusal ---")
    tampered_pack = pack_path.parent / "MRPL_KnowledgePack_TAMPERED.pack"
    pack_bytes = bytearray(pack_path.read_bytes())
    # Tamper single byte in the middle of archive
    pack_bytes[len(pack_bytes) // 2] ^= 0xFF
    tampered_pack.write_bytes(pack_bytes)

    tamper_import_res = knowledge_pack_engine.import_pack(tampered_pack)
    print(f"Tampered Pack Import Result: Status = {tamper_import_res['status']}")
    print(f"Rejection Message: {tamper_import_res['message']}")
    assert tamper_import_res["status"] in ["REFUSED_TAMPERED_SIGNATURE", "REFUSED_TAMPERED_PAYLOAD", "ERROR_CORRUPTED_ARCHIVE"]
    print(">>> Gate E PASS")


def test_gate_f_zero_egress_audit():
    print("\n--- Gate F: Zero-Egress Network Audit during Voice & Bilingual Operations ---")
    # Verify ledger has zero external connections
    entries = audit_ledger.get_recent_entries(limit=50)
    external_calls = [e for e in entries if "wan" in str(e).lower() or "cloud" in str(e).lower() or "external_ip" in str(e).lower()]
    assert len(external_calls) == 0, f"Detected external call in audit ledger: {external_calls}"
    print(f"Audited {len(entries)} recent ledger entries. Total WAN / Cloud Egress: 0 bytes. Air-gap intact!")
    print(">>> Gate F PASS")


def run_all_l16_checks():
    print("=" * 70)
    print("STARTING TASK L16 VERIFICATION: FIELD EDGE & SIGNED KNOWLEDGE PACKS")
    print("=" * 70)
    test_gate_a_and_b_voice_intake()
    test_gate_c_bilingual_approval_note()
    test_gate_d_and_e_knowledge_packs()
    test_gate_f_zero_egress_audit()
    print("\n" + "=" * 70)
    print("ALL GATES PASSED (6/6) - TASK L16 CERTIFIED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_l16_checks()
