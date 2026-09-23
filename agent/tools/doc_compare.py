#!/usr/bin/env python3
"""
================================================================================
SIH 2026: DOCUMENT COMPARISON TOOL (TASK L19 - FEATURE 2)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Performs field-level diffing between two inspection reports or engineering specs.
Computes numerical deltas, direction indicators (WORSENED, IMPROVED, UNCHANGED,
CHANGED, MISSING), and outputs a structured diff matrix.
================================================================================
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

base_dir = Path(__file__).resolve().parent.parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from agent.tools.file_ingest import file_ingest
from agent.tools.field_extractor import field_extractor
from agent.tools.pdf_parser import pdf_parser
from agent.tools.vision_ocr import vision_ocr

class DocumentComparisonTool:
    def __init__(self):
        self.base_dir = base_dir

    def extract_document_fields(self, file_path: str) -> Dict[str, Any]:
        """
        Extracts structured fields from PDF, image, text, or JSON.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        
        # If already JSON
        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)

        if ext == ".pdf":
            # Try text extraction first
            parsed = pdf_parser.parse(file_path)
            extracted = field_extractor.extract_from_text(parsed.get("text", ""))
            # If equipment tag is empty, try vision OCR
            if not extracted.get("equipment_tag"):
                ocr_res = vision_ocr.extract_inspection_findings(file_path)
                if ocr_res.get("equipment_tag"):
                    return ocr_res
            return extracted

        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return vision_ocr.extract_inspection_findings(file_path)

        elif ext in [".txt", ".csv", ".docx"]:
            ingest_res = file_ingest.ingest(file_path)
            content = ingest_res.get("content", "")
            if isinstance(content, dict):
                return content
            return field_extractor.extract_from_text(str(content))

        # Fallback
        ingest_res = file_ingest.ingest(file_path)
        return field_extractor.extract_from_text(str(ingest_res.get("content", "")))

    def compare(self, file_path_a: str, file_path_b: str) -> Dict[str, Any]:
        """
        Compares two document files field-by-field.
        Document A is considered Baseline (T1 / Rev 0), Document B is Current (T2 / Rev 1).
        """
        data_a = self.extract_document_fields(file_path_a)
        data_b = self.extract_document_fields(file_path_b)

        return self.compare_extracted(data_a, data_b, label_a=os.path.basename(file_path_a), label_b=os.path.basename(file_path_b))

    def compare_extracted(
        self,
        data_a: Dict[str, Any],
        data_b: Dict[str, Any],
        label_a: str = "Baseline Document (Rev A)",
        label_b: str = "Current Document (Rev B)"
    ) -> Dict[str, Any]:
        """
        Compares two extracted data dictionaries.
        """
        diff_entries = []
        summary_stats = {
            "total_fields_compared": 0,
            "identical_fields": 0,
            "worsened_fields": 0,
            "improved_fields": 0,
            "changed_fields": 0,
            "missing_fields": 0
        }

        # Flatten or extract key comparison parameters
        tag_a = data_a.get("equipment_tag") or data_a.get("tag") or data_a.get("critical_defect", {}).get("equipment_tag") or "UNKNOWN"
        tag_b = data_b.get("equipment_tag") or data_b.get("tag") or data_b.get("critical_defect", {}).get("equipment_tag") or "UNKNOWN"

        crit_a = data_a.get("critical_defect") or data_a.get("computed_values") or {}
        crit_b = data_b.get("critical_defect") or data_b.get("computed_values") or {}

        # Standard field map: (Field Name, Key Path, Direction Type)
        # Direction Type:
        #   'lower_is_worse': e.g., wall thickness, remaining life
        #   'higher_is_worse': e.g., corrosion rate, pressure drop, defect depth
        #   'categorical': e.g., inspector, date, status, material
        field_definitions = [
            ("Equipment Tag", ["equipment_tag", "tag"], "categorical"),
            ("Plant / Unit", ["plant_unit", "unit"], "categorical"),
            ("Inspection Date", ["inspection_date", "date"], "categorical"),
            ("Component Name", ["critical_defect.component", "component"], "categorical"),
            ("Measured Thickness (mm)", ["critical_defect.measured_thickness_mm", "measured_thickness_mm", "thickness_mm"], "lower_is_worse"),
            ("Previous Thickness (mm)", ["critical_defect.previous_thickness_mm", "previous_thickness_mm"], "lower_is_worse"),
            ("Minimum Design Thickness (mm)", ["critical_defect.design_minimum_mm", "design_minimum_mm", "t_min_mm"], "categorical"),
            ("Nominal Thickness (mm)", ["critical_defect.nominal_thickness_mm", "nominal_thickness_mm"], "categorical"),
            ("Calculated Corrosion Rate (mm/yr)", ["critical_defect.calculated_corrosion_rate_mm_yr", "corrosion_rate_mm_yr", "cr_mm_yr"], "higher_is_worse"),
            ("Calculated Remaining Life (years)", ["critical_defect.calculated_remaining_life_years", "remaining_life_years", "rl_years"], "lower_is_worse"),
            ("Operating Pressure (bar/kg/cm2)", ["operating_pressure", "pressure_bar"], "categorical"),
            ("Operating Temperature (C)", ["operating_temperature", "temperature_c"], "categorical"),
            ("Material Spec", ["material", "metallurgy", "material_spec"], "categorical"),
            ("NDT Method", ["ndt_method", "inspection_method"], "categorical"),
            ("Action / Recommendation", ["action_required", "recommendation"], "categorical")
        ]

        def get_value(d: Dict[str, Any], keys: List[str]) -> Any:
            for k in keys:
                if "." in k:
                    parts = k.split(".")
                    sub = d
                    found = True
                    for p in parts:
                        if isinstance(sub, dict) and p in sub:
                            sub = sub[p]
                        else:
                            found = False
                            break
                    if found and sub is not None:
                        return sub
                else:
                    if k in d and d[k] is not None:
                        return d[k]
            return None

        for field_name, keys, dir_type in field_definitions:
            val_a = get_value(data_a, keys)
            val_b = get_value(data_b, keys)

            # If both are None and not a primary field, skip
            if val_a is None and val_b is None:
                continue

            summary_stats["total_fields_compared"] += 1
            delta = None
            direction = "UNCHANGED"
            delta_str = "0"

            if val_a is None and val_b is not None:
                direction = "ADDED_IN_REV_B"
                summary_stats["changed_fields"] += 1
                delta_str = "New field in Rev B"
            elif val_a is not None and val_b is None:
                direction = "MISSING_IN_REV_B"
                summary_stats["missing_fields"] += 1
                delta_str = "Removed in Rev B"
            else:
                # Both exist - compare
                # Check numerical
                num_a = self._to_float(val_a)
                num_b = self._to_float(val_b)

                if num_a is not None and num_b is not None:
                    delta = round(num_b - num_a, 4)
                    if abs(delta) < 1e-5:
                        direction = "UNCHANGED"
                        delta_str = "0.00"
                        summary_stats["identical_fields"] += 1
                    else:
                        delta_sign = "+" if delta > 0 else ""
                        delta_str = f"{delta_sign}{delta:.3f}"
                        if dir_type == "lower_is_worse":
                            if delta < 0:
                                direction = "WORSENED"
                                summary_stats["worsened_fields"] += 1
                            else:
                                direction = "IMPROVED"
                                summary_stats["improved_fields"] += 1
                        elif dir_type == "higher_is_worse":
                            if delta > 0:
                                direction = "WORSENED"
                                summary_stats["worsened_fields"] += 1
                            else:
                                direction = "IMPROVED"
                                summary_stats["improved_fields"] += 1
                        else:
                            direction = "CHANGED"
                            summary_stats["changed_fields"] += 1
                else:
                    # Categorical / string comparison
                    str_a = str(val_a).strip()
                    str_b = str(val_b).strip()
                    if str_a == str_b:
                        direction = "UNCHANGED"
                        delta_str = "Identical"
                        summary_stats["identical_fields"] += 1
                    else:
                        direction = "CHANGED"
                        delta_str = f"'{str_a}' -> '{str_b}'"
                        summary_stats["changed_fields"] += 1

            diff_entries.append({
                "field": field_name,
                "val_a": val_a if val_a is not None else "N/A",
                "val_b": val_b if val_b is not None else "N/A",
                "delta": delta_str,
                "direction": direction,
                "is_critical_change": direction in ["WORSENED", "MISSING_IN_REV_B"]
            })

        # Overall verdict
        if summary_stats["worsened_fields"] > 0:
            overall_status = "DEGRADATION_DETECTED"
            executive_verdict = f"Critical degradation detected across {summary_stats['worsened_fields']} integrity parameter(s). Engineering review required."
        elif summary_stats["improved_fields"] > 0 and summary_stats["worsened_fields"] == 0:
            overall_status = "IMPROVED"
            executive_verdict = "Integrity parameters show improvement (e.g. post-repair thickness or derated corrosion rate)."
        elif summary_stats["changed_fields"] > 0:
            overall_status = "MODIFIED"
            executive_verdict = "Non-degradative changes detected between revisions."
        else:
            overall_status = "IDENTICAL"
            executive_verdict = "Both document versions are identical in all structural and engineering fields."

        return {
            "status": "SUCCESS",
            "document_a": label_a,
            "document_b": label_b,
            "overall_status": overall_status,
            "executive_verdict": executive_verdict,
            "summary_stats": summary_stats,
            "diff_matrix": diff_entries,
            "equipment_tag_a": tag_a,
            "equipment_tag_b": tag_b,
            "same_equipment": str(tag_a).upper() == str(tag_b).upper()
        }

    def _to_float(self, val: Any) -> Optional[float]:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        try:
            # Strip out units like mm, bar, yr, %
            cleaned = re.sub(r'[^\d\.\-]', '', str(val))
            if cleaned and cleaned not in ['.', '-', '-.']:
                return float(cleaned)
        except Exception:
            pass
        return None

doc_compare = DocumentComparisonTool()

if __name__ == "__main__":
    # Quick self test
    test_a = {
        "equipment_tag": "V-101",
        "plant_unit": "CDU-1",
        "critical_defect": {
            "component": "Bottom Shell Course",
            "measured_thickness_mm": 11.2,
            "previous_thickness_mm": 12.0,
            "design_minimum_mm": 8.5,
            "calculated_corrosion_rate_mm_yr": 0.228,
            "calculated_remaining_life_years": 11.84
        }
    }
    test_b = {
        "equipment_tag": "V-101",
        "plant_unit": "CDU-1",
        "critical_defect": {
            "component": "Bottom Shell Course",
            "measured_thickness_mm": 10.4,
            "previous_thickness_mm": 11.2,
            "design_minimum_mm": 8.5,
            "calculated_corrosion_rate_mm_yr": 0.267,
            "calculated_remaining_life_years": 7.12
        }
    }
    res = doc_compare.compare_extracted(test_a, test_b, "2022 Inspection", "2026 Inspection")
    print(json.dumps(res, indent=2))
