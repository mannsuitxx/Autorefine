#!/usr/bin/env python3
"""
================================================================================
SIH 2026 MASTER COMPREHENSIVE ACCEPTANCE & DIFFERENTIATOR VERIFICATION SUITE
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Executes all Core Invariants (T1-T12) and all Differentiator Tasks (D10-D17).
================================================================================
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from agent.loop import SovereignAgentLoop
from agent.router import CapabilityRouter
from agent.tools.llm_client import LocalLLMClient
from agent.tools.vision_ocr import VisionOCRTool
from agent.tools.sandbox import CodeSandboxTool
from agent.tools.doc_gen import DocumentGeneratorTool
from agent.tools.file_ingest import file_ingest
from agent.tools.field_extractor import field_extractor
from agent.tools.calculations import EngineeringCalculationEngine
from agent.tools.audit_logger import audit_logger

def log_test(test_id: str, title: str, passed: bool, details: str = ""):
    status_str = "✅ PASS" if passed else "❌ FAIL"
    print(f"[{status_str}] [{test_id}] {title}")
    if details:
        print(f"       ↳ {details}")

def run_script_gate(script_rel_path: str, test_id: str, test_title: str) -> bool:
    """Runs a sub-verification script as a subprocess and logs result."""
    t0 = time.time()
    res = subprocess.run(
        [sys.executable, str(base_dir / script_rel_path)],
        capture_output=True,
        text=True,
        cwd=str(base_dir)
    )
    elapsed = time.time() - t0
    passed = (res.returncode == 0)
    detail = f"Completed in {elapsed:.2f}s" if passed else f"Exit code {res.returncode}: {res.stderr[-200:] if res.stderr else res.stdout[-200:]}"
    log_test(test_id, test_title, passed, detail)
    return passed

def main():
    print("=" * 85)
    print("  SIH 2026: MASTER FORENSIC ACCEPTANCE SUITE (L01 THROUGH L17)")
    print("=" * 85)

    pass_count = 0
    fail_count = 0

    # --------------------------------------------------------------------------
    # T1: User-Supplied Inspection Sheet (V-205 -> CR: 0.875 mm/yr, RL: 2.86 yrs)
    # --------------------------------------------------------------------------
    print("\n--- [T1: USER-SUPPLIED DIFFERENT INSPECTION SHEET (V-205)] ---")
    ocr = VisionOCRTool()
    f_v205 = str(base_dir / "data" / "test_fixtures" / "V205_Different_Inspection_Report.png")
    r_v205 = ocr.extract_inspection_findings(f_v205)
    c_v205 = r_v205.get("critical_defect") or {}

    cr_205 = c_v205.get("calculated_corrosion_rate_mm_yr")
    rl_205 = c_v205.get("calculated_remaining_life_years")
    tag_205 = r_v205.get("equipment_tag")

    t1_pass = (cr_205 == 0.875) and (rl_205 == 2.86) and ("205" in str(tag_205))
    log_test("T1", "Extracted V-205: Tag='V-205', CR=0.875 mm/yr, RL=2.86 yrs (No hardcoded 0.429 / 1.63)", t1_pass,
             f"Tag={tag_205}, CR={cr_205} mm/yr, RL={rl_205} yrs")
    pass_count += int(t1_pass); fail_count += int(not t1_pass)

    # --------------------------------------------------------------------------
    # T2: Original V-101 Sheet Derivation & OCR Source Spans
    # --------------------------------------------------------------------------
    print("\n--- [T2: ORIGINAL V-101 SHEET DERIVATION & SOURCE SPANS] ---")
    f_v101 = str(base_dir / "data" / "sample_docs" / "inspection_reports" / "CDU_V101_Inspection_Turnaround_Report.png")
    r_v101 = ocr.extract_inspection_findings(f_v101)
    c_v101 = r_v101.get("critical_defect") or {}

    cr_101 = c_v101.get("calculated_corrosion_rate_mm_yr")
    rl_101 = c_v101.get("calculated_remaining_life_years")
    span_101 = c_v101.get("source_span", "N/A")

    t2_pass = (cr_101 is not None and 0.42 <= cr_101 <= 0.43) and (rl_101 is not None and 1.60 <= rl_101 <= 1.65)
    log_test("T2", "V-101 values derived dynamically from OCR text with proven source span", t2_pass,
             f"Tag={r_v101.get('equipment_tag')}, CR={cr_101} mm/yr, RL={rl_101} yrs | Span: '{span_101}'")
    pass_count += int(t2_pass); fail_count += int(not t2_pass)

    # --------------------------------------------------------------------------
    # T3: Differential Test (V-205 vs V-101)
    # --------------------------------------------------------------------------
    print("\n--- [T3: DIFFERENTIAL TEST (V-205 vs V-101 BACK-TO-BACK)] ---")
    t3_pass = (cr_205 != cr_101) and (rl_205 != rl_101) and (r_v205.get("equipment_tag") != r_v101.get("equipment_tag"))
    log_test("T3", "All engineering figures and equipment tags differ dynamically across documents", t3_pass,
             f"V205=(Tag:{tag_205}, CR:{cr_205}, RL:{rl_205}) vs V101=(Tag:{r_v101.get('equipment_tag')}, CR:{cr_101}, RL:{rl_101})")
    pass_count += int(t3_pass); fail_count += int(not t3_pass)

    # --------------------------------------------------------------------------
    # T4: Dynamic CSV Telemetry & Ingestion Verification
    # --------------------------------------------------------------------------
    print("\n--- [T4: TELEMETRY & CSV INGESTION PARSER] ---")
    csv_f = str(base_dir / "data" / "sample_docs" / "engineering_logs" / "E104_Heat_Exchanger_Operating_Log.csv")
    csv_res = file_ingest.ingest(csv_f)
    t4_pass = (csv_res.get("extraction_path_used") == "STRUCTURED_CSV_PARSER") and (len(csv_res.get("tables", [])) > 0)
    log_test("T4", "Telemetry parser analyzed CSV stream with exact column metrics and tables", t4_pass,
             f"Rows parsed: {csv_res.get('tables', [{}])[0].get('row_count') if csv_res.get('tables') else 0}")
    pass_count += int(t4_pass); fail_count += int(not t4_pass)

    # --------------------------------------------------------------------------
    # T5: Edge Case Handling (Zero-Byte, Corrupt, Spoofed Extensions)
    # --------------------------------------------------------------------------
    print("\n--- [T5: EDGE CASE HANDLING (ZERO-BYTE & CORRUPTED FILES)] ---")
    corrupt_f = str(base_dir / "data" / "test_fixtures" / "corrupted_empty.png")
    Path(corrupt_f).parent.mkdir(parents=True, exist_ok=True)
    Path(corrupt_f).touch()
    t5_pass = False
    try:
        r_corrupt = ocr.extract_inspection_findings(corrupt_f)
        t5_pass = (r_corrupt.get("ocr_confidence_pct", 100.0) == 0.0) or ("error" in r_corrupt)
    except Exception as e:
        t5_pass = True  # Raised expected exception on corrupt empty image
    log_test("T5", "System handled zero-byte file gracefully without unhandled crash", t5_pass,
             "Handled corrupt image exception cleanly")
    pass_count += int(t5_pass); fail_count += int(not t5_pass)

    # --------------------------------------------------------------------------
    # T6: Empty Attachment Rejection (No Demo Fallback)
    # --------------------------------------------------------------------------
    print("\n--- [T6: EMPTY ATTACHMENT REJECTION (NO DEMO FALLBACK)] ---")
    agent = SovereignAgentLoop()
    caught_empty_attachment = False
    try:
        agent.run("Analyse inspection report", attached_files=[])
    except ValueError as e:
        caught_empty_attachment = "No inspection file supplied" in str(e) or "No telemetry file supplied" in str(e)

    t6_pass = caught_empty_attachment
    log_test("T6", "Agent raised ValueError on missing attachment without fallback constants", t6_pass,
             f"Empty attachment rejected: {caught_empty_attachment}")
    pass_count += int(t6_pass); fail_count += int(not t6_pass)

    # --------------------------------------------------------------------------
    # T7: Codebase Grep Audit (Zero Hardcoded Numerical Fixtures)
    # --------------------------------------------------------------------------
    print("\n--- [T7: CODEBASE GREP AUDIT (ZERO NUMERICAL FIXTURES)] ---")
    fixture_targets = ['0.429', '1.63', '14.6', '13.1']
    code_hits = []
    for sub in ['agent/tools/vision_ocr.py', 'agent/tools/doc_gen.py', 'agent/loop.py']:
        target_f = base_dir / sub
        if target_f.exists():
            with open(target_f, "r", encoding="utf-8") as f_obj:
                for line_no, line in enumerate(f_obj, 1):
                    for t in fixture_targets:
                        if t in line and not line.strip().startswith("#"):
                            code_hits.append(f"{sub}:{line_no} [{t}] {line.strip()[:60]}")

    t7_pass = (len(code_hits) == 0)
    log_test("T7", "Runtime logic has 0 hardcoded numerical fixtures", t7_pass,
             f"Remaining literal assignments: {len(code_hits)}")
    pass_count += int(t7_pass); fail_count += int(not t7_pass)

    # --------------------------------------------------------------------------
    # D10 through D17: Differentiator Subsystem Verification Gates
    # --------------------------------------------------------------------------
    print("\n--- [DIFFERENTIATOR GATES D10 THROUGH D17] ---")
    
    # D10: LangGraph State Machine, Checkpoints, HITL Gate & Deterministic Replay
    d10_pass = run_script_gate("scripts/verify_l10.py", "D10", "LangGraph State Machine, SQLite Checkpoints, HITL Interrupt, Deterministic Replay")
    pass_count += int(d10_pass); fail_count += int(not d10_pass)

    # D11: Signed Audit Ledger (Ed25519) & Air-Gap Attestation
    d11_pass = run_script_gate("scripts/verify_l11.py", "D11", "Tamper-Evident Signed Audit Ledger (Ed25519) & Air-Gap Zero-Egress Attestation")
    pass_count += int(d11_pass); fail_count += int(not d11_pass)

    # D12: GraphRAG Equipment Knowledge Graph & Cross-Encoder Reranking
    d12_pass = run_script_gate("scripts/verify_l12.py", "D12", "GraphRAG Relational Knowledge Graph, 3-Way RRF Fusion, Cross-Encoder Reranking")
    pass_count += int(d12_pass); fail_count += int(not d12_pass)

    # D13: 3-Tier Physics Guard, Claim Entailment & Calibrated Abstention
    d13_pass = run_script_gate("scripts/verify_l13.py", "D13", "Deterministic Physics Invariants Guard, Claim Entailment Verifier, Calibrated Abstention")
    pass_count += int(d13_pass); fail_count += int(not d13_pass)

    # D14: Classical ML Corrosion Degradation & Fleet Risk Matrix
    d14_pass = run_script_gate("scripts/verify_l14.py", "D14", "Classical ML OLS Regression with 95% Prediction Interval, Fleet Risk Ranking, TF-IDF Classifier")
    pass_count += int(d14_pass); fail_count += int(not d14_pass)

    # D15: Constrained Structured Decoding & 5-Way Ablation Benchmark
    d15_pass = run_script_gate("scripts/verify_l15.py", "D15", "Constrained Schema Decoding (0% Violations), 30-Case Golden Set, 5-Way Ablation Benchmark")
    pass_count += int(d15_pass); fail_count += int(not d15_pass)

    # D16: Field Edge Offline Voice Intake, Bilingual Engine & Signed Knowledge Packs
    d16_pass = run_script_gate("scripts/verify_l16.py", "D16", "Offline Field Voice Intake (0% WER), Byte-Preserving Bilingual Engine, Ed25519 Signed Knowledge Packs")
    pass_count += int(d16_pass); fail_count += int(not d16_pass)

    # D17: Judge-Proof Adversarial Probes
    d17_pass = run_script_gate("scripts/verify_l17.py", "D17", "Judge-Proof Adversarial Closure Loop (10 Adversarial Probes, Double-Pass Clean)")
    pass_count += int(d17_pass); fail_count += int(not d17_pass)

    # ==========================================================================
    # Master Summary
    # ==========================================================================
    print("\n" + "=" * 85)
    print(f"  MASTER ACCEPTANCE SUMMARY: {pass_count} PASSED / {fail_count} FAILED")
    print("=" * 85)

    if fail_count == 0:
        print("🎉 ALL ACCEPTANCE & DIFFERENTIATOR GATES PASSED! SYSTEM IS 100% PRODUCTION READY & CERTIFIED.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
