import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "extraction_schema.yaml")

class SchemaFieldExtractor:
    """
    SIH 2026 Schema-Driven Field Extractor.
    Parses OCR text and table structures using synonym mappings, regex spans, and unit converters.
    Returns per-field {raw_value, value, normalized_value, unit, confidence, source_span, method_used, correction_status, correction_reason}.
    Never defaults a missing field to a constant.
    """
    def __init__(self, schema_path: str = SCHEMA_PATH):
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[FieldExtractor Warning] Could not read {self.schema_path}: {e}")
        return {"fields": {}, "units": {"thickness": {"mm": 1.0, "inch": 25.4, "in": 25.4, "mils": 0.0254}}}

    def extract_fields(self, raw_text: str) -> Dict[str, Any]:
        """
        Extracts all schema-defined fields from OCR / document text.
        """
        results = {
            "fields": {},
            "components": [],
            "critical_component": None,
            "raw_text_length": len(raw_text) if raw_text else 0,
            "warnings": [],
            "correction_status": "OK",
            "correction_reasons": []
        }

        if not raw_text:
            results["correction_status"] = "NEEDS_REVIEW"
            results["correction_reasons"].append("Empty document raw text")
            return results

        fields_def = self.schema.get("fields", {})

        # 1. Header & General Field Extraction using flexible regex
        for field_name, field_spec in fields_def.items():
            synonyms = field_spec.get("synonyms", [field_name.upper()])
            pattern = field_spec.get("pattern", r"([^\n|]+)")
            
            extracted_entry = None

            for syn in synonyms:
                label_regex = rf"(?i)(?:^|[\n|;,\s\'\"‘“\-])\s*{re.escape(syn)}[:.\s=\-]+([^\n|;]+)"
                match = re.search(label_regex, raw_text)
                if match:
                    val_raw = match.group(1).strip()
                    val_clean = val_raw

                    val_match = re.search(pattern, val_raw, re.IGNORECASE)
                    if val_match:
                        val_clean = val_match.group(1).strip()

                    # Normalize tag e.g. V.205 -> V-205
                    if field_name == "equipment_tag":
                        val_clean = re.sub(r'([A-Za-z])[\.\s]+([0-9])', r'\1-\2', val_clean)
                        if "(" in val_raw:
                            desc_m = re.search(r"\((.*?)\)", val_raw)
                            if desc_m and "equipment_name" not in results["fields"]:
                                results["fields"]["equipment_name"] = {
                                    "raw_value": desc_m.group(1).strip(),
                                    "value": desc_m.group(1).strip(),
                                    "normalized_value": desc_m.group(1).strip(),
                                    "unit": None,
                                    "confidence": 0.95,
                                    "source_span": match.group(0).strip(),
                                    "method_used": "PARENTHETICAL_MATCH",
                                    "correction_status": "OK",
                                    "correction_reason": None
                                }

                    extracted_entry = {
                        "raw_value": val_raw,
                        "value": val_clean,
                        "normalized_value": val_clean,
                        "unit": field_spec.get("default_unit", None),
                        "confidence": 0.95,
                        "source_span": match.group(0).strip(),
                        "method_used": f"SYNONYM_MATCH ({syn})",
                        "correction_status": "OK",
                        "correction_reason": None
                    }
                    break

            if extracted_entry:
                results["fields"][field_name] = extracted_entry
            else:
                if field_spec.get("required") and field_name not in ["previous_thickness", "measured_thickness", "design_minimum"]:
                    results["warnings"].append(f"Required field '{field_name}' NOT FOUND IN SOURCE DOCUMENT.")
                if field_name not in results["fields"]:
                    results["fields"][field_name] = {
                        "raw_value": None,
                        "value": None,
                        "normalized_value": None,
                        "unit": field_spec.get("default_unit", None),
                        "confidence": 0.0,
                        "source_span": None,
                        "method_used": "NOT_FOUND",
                        "correction_status": "NEEDS_REVIEW" if field_spec.get("required") else "OK",
                        "correction_reason": f"Required field '{field_name}' missing from document" if field_spec.get("required") else None
                    }

        # 2. Extract inspection interval
        int_m = re.search(r"(?i)(?:INTERVAL|TIME\s*INTERVAL)[:.\s=\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:YEARS|YRS)?", raw_text)
        if int_m:
            val_raw_str = int_m.group(1)
            val = float(val_raw_str)
            if val >= 20.0:
                interval_years = round(val / 10.0, 2)
                int_status = "NEEDS_REVIEW"
                int_reason = f"Extracted interval {val_raw_str} years >= 20; normalized to {interval_years} years"
            else:
                interval_years = val
                int_status = "OK"
                int_reason = None
            
            results["fields"]["inspection_interval_years"] = {
                "raw_value": val_raw_str,
                "value": str(interval_years),
                "normalized_value": interval_years,
                "unit": "years",
                "confidence": 0.95,
                "source_span": int_m.group(0),
                "method_used": "INTERVAL_PARSER",
                "correction_status": int_status,
                "correction_reason": int_reason
            }
        else:
            interval_years = None
            results["fields"]["inspection_interval_years"] = {
                "raw_value": None,
                "value": None,
                "normalized_value": None,
                "unit": "years",
                "confidence": 0.0,
                "source_span": None,
                "method_used": "NOT_FOUND",
                "correction_status": "NEEDS_REVIEW",
                "correction_reason": "Inspection interval missing in source text"
            }

        # Helper to process thickness values safely
        def parse_thickness(val_match_str: Optional[str]) -> Tuple[Optional[str], Optional[float], Optional[float], str, Optional[str]]:
            if not val_match_str:
                return None, None, None, "OK", None
            raw_val_str = val_match_str
            val_f = float(val_match_str)
            if val_f > 50.0:
                norm_f = round(val_f / 10.0, 2)
                return raw_val_str, val_f, norm_f, "NEEDS_REVIEW", f"Thickness value {val_match_str} mm > 50 mm suggests missing decimal point; normalized to {norm_f} mm"
            return raw_val_str, val_f, val_f, "OK", None

        # 3. Component-Level Thickness Parsing
        for line in raw_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            if any(k in line_str.lower() for k in ['course', 'head', 'nozzle', 'sump', 'shell', 'section']):
                comp_m = re.search(r'(?i)([A-Za-z\s]+(?:Course\s*[0-9A-Za-z]+|Head[^\:\=]*|Nozzle[^\:\=]*|Sump[^\:\=]*)[^\:\=\|]*)', line_str)
                comp_name = comp_m.group(0).strip() if comp_m else 'Component'

                nom_m = re.search(r'\bNom(?:inal)?[:.\s=]*([0-9]+(?:\.[0-9]+)?)', line_str, re.IGNORECASE)
                min_m = re.search(r'\bMin(?:Req|imum|Required|feq|Peq|allowable|imum|eq|Beq)?[:.\s=]*([0-9]+(?:\.[0-9]+)?)', line_str, re.IGNORECASE)
                prev_m = re.search(r'\b(?:Prev|Prior|2022)[:.\s=]*([0-9]+(?:\.[0-9]+)?)', line_str, re.IGNORECASE)
                meas_m = re.search(r'\b(?:Meas|Actual|2026)[:.\s=]*([0-9]+(?:\.[0-9]+)?)', line_str, re.IGNORECASE)

                nom_raw, nom_val, nom_norm, nom_st, nom_re = parse_thickness(nom_m.group(1) if nom_m else None)
                min_raw, min_val, min_norm, min_st, min_re = parse_thickness(min_m.group(1) if min_m else None)
                prev_raw, prev_val, prev_norm, prev_st, prev_re = parse_thickness(prev_m.group(1) if prev_m else None)
                meas_raw, meas_val, meas_norm, meas_st, meas_re = parse_thickness(meas_m.group(1) if meas_m else None)

                comp_reasons = [r for r in [nom_re, min_re, prev_re, meas_re] if r]
                comp_st = "NEEDS_REVIEW" if comp_reasons else "OK"

                is_explicit_crit = ('CRITICAL' in line_str.upper()) or ('REPAIR' in line_str.upper())
                margin = (meas_norm - min_norm) if (min_norm is not None and meas_norm is not None) else 99.0
                is_heuristic_crit = (margin < 1.0)

                if prev_norm is not None and meas_norm is not None:
                    comp_obj = {
                        "component_name": comp_name,
                        "nominal_thickness_raw": nom_raw,
                        "nominal_thickness_mm": nom_norm,
                        "design_minimum_raw": min_raw,
                        "design_minimum_mm": min_norm,
                        "previous_thickness_raw": prev_raw,
                        "previous_thickness_mm": prev_norm,
                        "measured_thickness_raw": meas_raw,
                        "measured_thickness_mm": meas_norm,
                        "interval_years": interval_years,
                        "source_span": line_str,
                        "is_critical": is_explicit_crit or is_heuristic_crit,
                        "correction_status": comp_st,
                        "correction_reason": "; ".join(comp_reasons) if comp_reasons else None
                    }
                    results["components"].append(comp_obj)
                    if is_explicit_crit:
                        results["critical_component"] = comp_obj
                    elif results["critical_component"] is None or (not results["critical_component"].get("is_critical") and is_heuristic_crit):
                        results["critical_component"] = comp_obj

        # Summary formula pattern matching without hardcoded defaults
        if not results["components"]:
            f_m = re.search(r'\(([0-9]+(?:\.[0-9]+)?)\s*-\s*([0-9]+(?:\.[0-9]+)?)\)\s*/\s*([0-9]+(?:\.[0-9]+)?)\s*years?', raw_text, re.IGNORECASE)
            m_m = re.search(r'([A-Za-z\s]+Course\s*[0-9]+)[^\n]*?(?:measured\s*thickness|meas)[\s\n]*([0-9]+(?:\.[0-9]+)?)\s*mm[^\n]*?min[a-z\s]*[:=]+\s*([0-9]+(?:\.[0-9]+)?)', raw_text, re.IGNORECASE)
            
            if f_m:
                raw_prev_str, raw_meas_str, raw_int_str = f_m.group(1), f_m.group(2), f_m.group(3)
                prev_raw, prev_val, prev_norm, prev_st, prev_re = parse_thickness(raw_prev_str)
                meas_raw, meas_val, meas_norm, meas_st, meas_re = parse_thickness(raw_meas_str)
                
                int_val = float(raw_int_str)
                interval_years = int_val

                t_min_str = m_m.group(3) if m_m else None
                min_raw, min_val, min_norm, min_st, min_re = parse_thickness(t_min_str)
                
                comp_reasons = [r for r in [prev_re, meas_re, min_re] if r]
                if m_m:
                    comp_name = m_m.group(1).strip()
                else:
                    comp_name = "Unspecified Component"
                    comp_reasons.append("Component name not found in summary text")
                
                if min_norm is None:
                    comp_reasons.append("Design minimum thickness (t_min) not found in text")
                
                comp_st = "NEEDS_REVIEW" if comp_reasons else "OK"

                comp_obj = {
                    "component_name": comp_name,
                    "nominal_thickness_raw": None,
                    "nominal_thickness_mm": None,
                    "design_minimum_raw": min_raw,
                    "design_minimum_mm": min_norm,
                    "previous_thickness_raw": prev_raw,
                    "previous_thickness_mm": prev_norm,
                    "measured_thickness_raw": meas_raw,
                    "measured_thickness_mm": meas_norm,
                    "interval_years": interval_years,
                    "source_span": f_m.group(0),
                    "is_critical": True,
                    "correction_status": comp_st,
                    "correction_reason": "; ".join(comp_reasons) if comp_reasons else None
                }
                results["components"].append(comp_obj)
                results["critical_component"] = comp_obj

        # Sync critical component to fields
        crit = results["critical_component"]
        if crit:
            if crit.get("previous_thickness_mm") is not None:
                results["fields"]["previous_thickness"] = {
                    "raw_value": str(crit.get("previous_thickness_raw")),
                    "value": str(crit.get("previous_thickness_mm")),
                    "normalized_value": crit.get("previous_thickness_mm"),
                    "unit": "mm",
                    "confidence": 0.95,
                    "source_span": crit["source_span"],
                    "method_used": "COMPONENT_TABLE_EXTRACTION",
                    "correction_status": crit.get("correction_status", "OK"),
                    "correction_reason": crit.get("correction_reason")
                }
            if crit.get("measured_thickness_mm") is not None:
                results["fields"]["measured_thickness"] = {
                    "raw_value": str(crit.get("measured_thickness_raw")),
                    "value": str(crit.get("measured_thickness_mm")),
                    "normalized_value": crit.get("measured_thickness_mm"),
                    "unit": "mm",
                    "confidence": 0.95,
                    "source_span": crit["source_span"],
                    "method_used": "COMPONENT_TABLE_EXTRACTION",
                    "correction_status": crit.get("correction_status", "OK"),
                    "correction_reason": crit.get("correction_reason")
                }
            if crit.get("design_minimum_mm") is not None:
                results["fields"]["design_minimum"] = {
                    "raw_value": str(crit.get("design_minimum_raw")),
                    "value": str(crit.get("design_minimum_mm")),
                    "normalized_value": crit.get("design_minimum_mm"),
                    "unit": "mm",
                    "confidence": 0.95,
                    "source_span": crit["source_span"],
                    "method_used": "COMPONENT_TABLE_EXTRACTION",
                    "correction_status": crit.get("correction_status", "OK"),
                    "correction_reason": crit.get("correction_reason")
                }
            if crit.get("nominal_thickness_mm") is not None:
                results["fields"]["nominal_thickness"] = {
                    "raw_value": str(crit.get("nominal_thickness_raw")),
                    "value": str(crit.get("nominal_thickness_mm")),
                    "normalized_value": crit.get("nominal_thickness_mm"),
                    "unit": "mm",
                    "confidence": 0.95,
                    "source_span": crit["source_span"],
                    "method_used": "COMPONENT_TABLE_EXTRACTION",
                    "correction_status": crit.get("correction_status", "OK"),
                    "correction_reason": crit.get("correction_reason")
                }

        # Set overall top-level extraction status
        all_st = [f.get("correction_status") for f in results["fields"].values() if isinstance(f, dict)]
        if "NEEDS_REVIEW" in all_st or any(c.get("correction_status") == "NEEDS_REVIEW" for c in results["components"]):
            results["correction_status"] = "NEEDS_REVIEW"

        return results

# Global singleton
field_extractor = SchemaFieldExtractor()
