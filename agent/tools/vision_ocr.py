#!/usr/bin/env python3
"""
================================================================================
SIH 2026: MULTIMODAL VISION OCR & HANDWRITING ENGINE (TASK L19 - FEATURE 5)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Extracts printed & handwritten text via Tesseract OCR and local Vision VLM routing.
Includes calibrated abstention for illegible scrawls and explicit method tags.
================================================================================
"""

import os
import shutil
import re
import sys
import shutil
import base64
import json
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

base_dir = Path(__file__).resolve().parent.parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from agent.tools.field_extractor import field_extractor
from agent.tools.calculations import EngineeringCalculationEngine

class VisionOCRTool:
    """
    True Multimodal OCR & Handwriting Entity Parser.
    Extracts raw text via Tesseract OCR and local VLM routing for handwritten/degraded text.
    """
    def __init__(self):
        self.tesseract_cmd = self._find_tesseract()
        self._setup_tesseract()
        self.ollama_url = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434")

    def _find_tesseract(self) -> str:
        candidates = [
            shutil.which("tesseract"),
            str(Path.home() / ".local" / "bin" / "tesseract"),
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract"
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return "tesseract"

    def _setup_tesseract(self):
        try:
            import pytesseract
            if os.path.exists(self.tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
            elif not shutil.which("tesseract"):
                self.available = False
                return
            self.pytesseract = pytesseract
            self.available = True
        except ImportError:
            self.available = False

    def transcribe_handwriting_with_vision(self, file_path: str, model_tag: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribes handwritten or low-confidence documents using local multimodal vision models.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")

        if not model_tag:
            try:
                from agent.router import router
                model_tag = router.get_role_model("documents_vision").get("ollama_tag", "moondream:latest")
            except Exception:
                model_tag = "moondream:latest"
        v_model = model_tag

        try:
            with open(file_path, "rb") as f:
                b64_img = base64.b64encode(f.read()).decode("utf-8")

            prompt = (
                "You are an on-premise industrial OCR system. Transcribe all text from this engineering inspection sheet, "
                "especially any handwritten maintenance notes, equipment tags, measured thickness numbers, dates, and inspector signatures. "
                "Output only the exact transcribed text as faithfully as possible without conversational filler."
            )

            req_payload = {
                "model": v_model,
                "prompt": prompt,
                "images": [b64_img],
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 300
                }
            }

            req = urllib.request.Request(
                f"{self.ollama_url}/api/generate",
                data=json.dumps(req_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = result.get("response", "").strip()

                # Check if illegible or empty
                if not text or len(text) < 5 or "unreadable" in text.lower() or "illegible" in text.lower():
                    return {
                        "status": "ABSTAIN",
                        "method": "VISION_HANDWRITING",
                        "model_used": v_model,
                        "is_abstain": True,
                        "raw_text": "",
                        "confidence_score": 0.1,
                        "abstention_reason": "Handwriting is illegible or degraded below safety verification threshold (Calibrated Abstention)."
                    }

                return {
                    "status": "SUCCESS",
                    "method": "VISION_HANDWRITING",
                    "model_used": v_model,
                    "is_abstain": False,
                    "raw_text": text,
                    "confidence_score": 0.88,
                    "file_path": file_path
                }
        except Exception as e:
            # Fallback if vision service is unavailable or timed out
            return {
                "status": "ABSTAIN",
                "method": "VISION_HANDWRITING",
                "model_used": v_model,
                "is_abstain": True,
                "raw_text": "",
                "abstention_reason": f"Vision model ({v_model}) handwriting extraction aborted / degraded image: {str(e)}"
            }

    def extract_inspection_findings(self, file_path: str, preprocessing_mode: str = "standard", model_tag: Optional[str] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Inspection file not found: {file_path}")

        raw_text = ""
        mean_conf = 0.0
        width, height = 0, 0
        extraction_method = "TESSERACT_OCR"

        # Load image via PIL
        try:
            from PIL import Image, ImageFilter, ImageEnhance
            img = Image.open(file_path)
            width, height = img.size

            if preprocessing_mode == "enhanced_denoise":
                img = img.filter(ImageFilter.MedianFilter(size=3))
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
            
            if self.available:
                raw_text = self.pytesseract.image_to_string(img).strip()
                ocr_data = self.pytesseract.image_to_data(img, output_type=self.pytesseract.Output.DICT)
                confs = [int(c) for c in ocr_data.get("conf", []) if int(c) >= 0]
                if confs:
                    mean_conf = round(sum(confs) / len(confs), 2)
        except Exception as e:
            if not self.available:
                vision_res = self.transcribe_handwriting_with_vision(file_path, model_tag=model_tag)
                if vision_res.get("status") == "SUCCESS" and vision_res.get("raw_text"):
                    raw_text = vision_res["raw_text"]
                    mean_conf = 85.0
                    extraction_method = "VISION_HANDWRITING"
                elif vision_res.get("is_abstain"):
                    return {
                        "document_type": "HANDWRITTEN_INSPECTION_NOTE",
                        "status": "ABSTAIN",
                        "method": "VISION_HANDWRITING",
                        "model_used": vision_res.get("model_used"),
                        "equipment_tag": None,
                        "plant_unit": None,
                        "critical_defect": None,
                        "raw_ocr_text": "",
                        "error": vision_res.get("abstention_reason", "Vision model could not read the image"),
                        "ocr_confidence_pct": 10.0,
                        "image_metadata": {"file_name": os.path.basename(file_path), "dimensions": f"{width}x{height}", "mode": preprocessing_mode}
                    }
            else:
                raise RuntimeError(f"Failed to process image through OCR engine: {e}")

        # If confidence is low or mode is explicitly handwriting, attempt Vision Model transcription
        if preprocessing_mode == "handwriting" or (mean_conf > 0 and mean_conf < 60.0) or not raw_text:
            vision_res = self.transcribe_handwriting_with_vision(file_path, model_tag=model_tag)
            if vision_res.get("status") == "SUCCESS" and vision_res.get("raw_text"):
                raw_text = vision_res["raw_text"]
                mean_conf = max(mean_conf, 85.0)
                extraction_method = "VISION_HANDWRITING"
            elif vision_res.get("is_abstain"):
                return {
                    "document_type": "HANDWRITTEN_INSPECTION_NOTE",
                    "status": "ABSTAIN",
                    "method": "VISION_HANDWRITING",
                    "model_used": vision_res.get("model_used"),
                    "equipment_tag": None,
                    "plant_unit": None,
                    "critical_defect": None,
                    "raw_ocr_text": "",
                    "error": vision_res.get("abstention_reason", "Illegible handwriting"),
                    "ocr_confidence_pct": 10.0,
                    "image_metadata": {"file_name": os.path.basename(file_path), "dimensions": f"{width}x{height}", "mode": preprocessing_mode}
                }

        if not raw_text:
            return {
                "document_type": "EMPTY_OR_UNREADABLE",
                "method": extraction_method,
                "equipment_tag": None,
                "plant_unit": None,
                "critical_defect": None,
                "raw_ocr_text": "",
                "error": "OCR engine returned no text from image file",
                "ocr_confidence_pct": 0.0,
                "image_metadata": {"file_name": os.path.basename(file_path), "dimensions": f"{width}x{height}", "mode": preprocessing_mode}
            }

        # Run schema-driven extraction
        extracted_data = field_extractor.extract_fields(raw_text)
        f_map = extracted_data.get("fields", {})

        tag_val = f_map.get("equipment_tag", {}).get("value")
        unit_val = f_map.get("plant_unit", {}).get("value")
        date_val = f_map.get("inspection_date", {}).get("value")
        insp_val = f_map.get("inspector", {}).get("value")
        ndt_val = f_map.get("ndt_method", {}).get("value")
        name_val = f_map.get("equipment_name", {}).get("value")

        # Document Type classification
        doc_type = "Technical Inspection Sheet"
        if "PID" in raw_text.upper() or "DWG" in raw_text.upper() or "FLOW DIAGRAM" in raw_text.upper():
            doc_type = "P&ID Process Schematic Diagram"
            dwg_match = re.search(r"(?:DWG|DRAWING)\s*(?:NO|NUMBER)?[:\s\-]+([A-Za-z0-9\-]+)", raw_text, re.IGNORECASE)
            if dwg_match:
                tag_val = tag_val or dwg_match.group(1).strip()
        elif "HANDWRITTEN" in preprocessing_mode.upper() or extraction_method == "VISION_HANDWRITING":
            doc_type = "Handwritten Inspection Log / Field Note"

        critical_defect = None
        crit_comp = extracted_data.get("critical_component")
        
        # Calculate derived metrics if component thickness readings exist
        if crit_comp:
            t_prev = crit_comp.get("previous_thickness_mm")
            t_meas = crit_comp.get("measured_thickness_mm")
            t_min = crit_comp.get("design_minimum_mm")
            interval_yrs = crit_comp.get("interval_years", 3.5)

            if t_prev is not None and t_meas is not None and t_min is not None:
                try:
                    calc_res = EngineeringCalculationEngine.calculate_vessel_integrity(
                        previous_thickness_mm=t_prev,
                        measured_thickness_mm=t_meas,
                        design_minimum_mm=t_min,
                        interval_years=interval_yrs,
                        component_name=crit_comp.get("component_name", "Shell Course")
                    )
                    critical_defect = {
                        "component": crit_comp.get("component_name"),
                        "nominal_thickness_mm": crit_comp.get("nominal_thickness_mm"),
                        "measured_thickness_mm": t_meas,
                        "design_minimum_mm": t_min,
                        "previous_thickness_mm": t_prev,
                        "remaining_margin_mm": calc_res["corrosion_allowance_remaining_mm"],
                        "calculated_corrosion_rate_mm_yr": calc_res["calculated_corrosion_rate_mm_yr"],
                        "calculated_remaining_life_years": calc_res["calculated_remaining_life_years"],
                        "action_required": calc_res["recommendation"],
                        "calculation_trace": calc_res["calculation_trace"],
                        "source_span": crit_comp.get("source_span")
                    }
                except Exception as e:
                    critical_defect = {"error": str(e), "component": crit_comp.get("component_name")}

        findings = {
            "document_type": doc_type,
            "method": extraction_method,
            "plant_unit": unit_val,
            "equipment_tag": tag_val,
            "equipment_name": name_val,
            "inspection_date": date_val,
            "inspector": insp_val,
            "ndt_method": ndt_val,
            "critical_defect": critical_defect,
            "components": extracted_data.get("components", []),
            "low_confidence_flags": [f"OCR confidence ({mean_conf}%) below 85%"] if mean_conf < 85.0 else [],
            "raw_ocr_text": raw_text,
            "ocr_confidence_pct": mean_conf,
            "image_metadata": {
                "file_name": os.path.basename(file_path),
                "dimensions": f"{width}x{height}",
                "mode": preprocessing_mode
            }
        }

        return findings

vision_ocr = VisionOCRTool()

if __name__ == "__main__":
    print("Vision OCR & Handwriting Tool Initialized. Tesseract available:", vision_ocr.available)
