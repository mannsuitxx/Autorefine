#!/usr/bin/env python3
"""
Characterization Test Suite for P0-A, P0-B, and P0-C.
Verifies fix for P0-A (field extraction integrity) and reports baseline state for P0-B and P0-C.
"""

import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

def test_p0_a_field_extraction_characterization():
    print("=== Testing P0-A: Field Extraction Integrity ===")
    from agent.tools.field_extractor import field_extractor

    # 1. Test unseen values (different from V-101: 18.0, 12.4, 14.6, 13.1, 3.5)
    raw_text = (
        "EQUIPMENT TAG: V-909 (Fractionator Vessel)\n"
        "INSPECTION DATE: 2026-05-10\n"
        "Course 1 Shell: Nom 19.5 mm, MinReq 11.8 mm, Prev 15.2 mm, Meas 13.7 mm\n"
        "INTERVAL: 5.0 YEARS\n"
    )
    res = field_extractor.extract_fields(raw_text)
    comp = res["critical_component"] if res.get("critical_component") else (res["components"][0] if res.get("components") else None)
    
    assert comp is not None, "Failed to extract component"
    print(f"Extracted component: {comp}")
    
    errors = []
    # Check for hardcoded fixture fallbacks
    if comp.get("nominal_thickness_mm") == 18.0:
        errors.append("nominal_thickness_mm fell back to hardcoded 18.0!")
    if comp.get("design_minimum_mm") == 12.4:
        errors.append("design_minimum_mm fell back to hardcoded 12.4!")
    if comp.get("previous_thickness_mm") == 14.6:
        errors.append("previous_thickness_mm fell back to hardcoded 14.6!")
    if comp.get("measured_thickness_mm") == 13.1:
        errors.append("measured_thickness_mm fell back to hardcoded 13.1!")
        
    # Check exact unseen value preservation
    if comp.get("nominal_thickness_mm") != 19.5:
        errors.append(f"Expected nominal 19.5, got {comp.get('nominal_thickness_mm')}")
    if comp.get("design_minimum_mm") != 11.8:
        errors.append(f"Expected min 11.8, got {comp.get('design_minimum_mm')}")
    if comp.get("previous_thickness_mm") != 15.2:
        errors.append(f"Expected prev 15.2, got {comp.get('previous_thickness_mm')}")
    if comp.get("measured_thickness_mm") != 13.7:
        errors.append(f"Expected meas 13.7, got {comp.get('measured_thickness_mm')}")

    # Check structure preservation
    f_prev = res["fields"].get("previous_thickness", {})
    if "raw_value" not in f_prev or "normalized_value" not in f_prev or "source_span" not in f_prev:
        errors.append("Missing raw_value, normalized_value, or source_span in field schema")

    # 2. Test missing fields (should not invent values or default interval to 3.5)
    missing_text = (
        "EQUIPMENT TAG: V-303\n"
        "Course 1 Shell: Meas 12.0 mm\n"
    )
    res_missing = field_extractor.extract_fields(missing_text)
    interval_entry = res_missing["fields"].get("inspection_interval_years", {})

    print(f"Missing text interval field: {interval_entry}")
    if interval_entry.get("normalized_value") == 3.5 or interval_entry.get("value") == "3.5":
        errors.append("inspection_interval_years defaulted to hardcoded 3.5 when omitted!")
    if interval_entry.get("correction_status") != "NEEDS_REVIEW":
        errors.append("Missing required field did not flag correction_status = 'NEEDS_REVIEW'")

    # 3. Test values > 50 mm (should preserve raw text, set normalized value, and mark NEEDS_REVIEW)
    high_text = "Course 1 Shell: Nom 220 mm, Min 124 mm, Prev 146 mm, Meas 131 mm"
    res_high = field_extractor.extract_fields(high_text)
    comp_h = res_high["critical_component"] if res_high.get("critical_component") else (res_high["components"][0] if res_high.get("components") else None)
    
    if comp_h:
        print(f"High value component: {comp_h}")
        if comp_h.get("correction_status") != "NEEDS_REVIEW":
            errors.append("Thickness > 50 mm was processed without setting correction_status = 'NEEDS_REVIEW'")
        if comp_h.get("measured_thickness_raw") != "131":
            errors.append(f"Raw thickness text not preserved for value > 50 mm: got {comp_h.get('measured_thickness_raw')}")
        if comp_h.get("measured_thickness_mm") != 13.1:
            errors.append(f"Normalized thickness incorrect for value > 50 mm: got {comp_h.get('measured_thickness_mm')}")

    if errors:
        print("P0-A Characterization Test FAILURES:")
        for err in errors:
            print("  -", err)
        return False
    else:
        print("P0-A Characterization Test PASSED!")
        return True


def test_p0_b_attestation_characterization():
    print("\n=== Testing P0-B: Air-Gap Attestation Integrity ===")
    from security.attest import AirgapAttestationEngine
    engine = AirgapAttestationEngine()
    hashes = engine._get_model_hashes()
    print("Model hashes in attest.py:", hashes)
    hardcoded = False
    for m in hashes:
        if m["sha256"] == "5c00e16eb710a9a1d13f9f4b1e5ad678a8f4c1e194827d0925e016f4ad59132c":
            hardcoded = True
    if hardcoded:
        print("P0-B Finding: Model hashes are hardcoded fixture strings in attest.py")
    return not hardcoded


def test_p0_c_model_routing_characterization():
    print("\n=== Testing P0-C: Model Routing Integrity ===")
    from agent.tools.vision_ocr import VisionOCRTool
    import inspect
    ocr = VisionOCRTool()
    src = inspect.getsource(ocr.transcribe_handwriting_with_vision)
    if '"model": "moondream:latest"' in src:
        print("P0-C Finding: Vision OCR directly hardcodes 'moondream:latest' bypassing router resolution.")
        return False
    return True


if __name__ == "__main__":
    a_pass = test_p0_a_field_extraction_characterization()
    b_pass = test_p0_b_attestation_characterization()
    c_pass = test_p0_c_model_routing_characterization()
    print(f"\nSummary: P0-A={a_pass}, P0-B={b_pass}, P0-C={c_pass}")
    sys.exit(0 if a_pass else 1)
