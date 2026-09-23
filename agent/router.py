#!/usr/bin/env python3
"""
================================================================================
SIH 2026: HARDWARE-ADAPTIVE CAPABILITY ROUTER (TASK L20)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Integrates hardware/detect.py and config/model_registry.yaml to dynamically
route requests across 5 role-models (STANDARD vs HIGH_RESOURCE profiles).
================================================================================
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from hardware.detect import detect, HardwareDetector
from agent.tools.audit_logger import audit_logger

class CapabilityRouter:
    """
    Hardware-Adaptive Capability Router.
    Routes industrial queries across 5 specialized roles according to the active hardware profile:
    1. general_reasoning_multimodal
    2. coding_agent
    3. deep_reasoning_calc
    4. documents_vision
    5. cpu_fallback
    """
    def __init__(self, simulate_ram: Optional[float] = None, simulate_vram: Optional[float] = None):
        self.detector = HardwareDetector()
        self.hardware_state = self.detector.detect_and_select_profile(
            simulate_ram=simulate_ram,
            simulate_vram=simulate_vram
        )
        self.active_profile = self.hardware_state.get("active_profile", "STANDARD")
        self.models_map = self.hardware_state.get("models", {})

    def reload(self, simulate_ram: Optional[float] = None, simulate_vram: Optional[float] = None) -> Dict[str, Any]:
        """Re-evaluates hardware metrics and updates the active profile."""
        self.hardware_state = self.detector.detect_and_select_profile(
            simulate_ram=simulate_ram,
            simulate_vram=simulate_vram
        )
        self.active_profile = self.hardware_state.get("active_profile", "STANDARD")
        self.models_map = self.hardware_state.get("models", {})
        return self.hardware_state

    def get_role_model(self, role_key: str) -> Dict[str, Any]:
        """Returns model specification for a given role under the active profile."""
        if role_key in self.models_map:
            return self.models_map[role_key]
        return self.models_map.get("general_reasoning_multimodal", {
            "ollama_tag": "qwen3.5:9b",
            "fallback_tag": "qwen2.5:1.5b",
            "license": "Apache 2.0",
            "role": "General Reasoning & SOP Compliance"
        })

    def route(self, prompt: str, attached_files: Optional[List[str]] = None) -> Dict[str, Any]:
        p = prompt.lower()
        files = attached_files or []
        has_img = any(f.lower().endswith((".png", ".jpg", ".jpeg", ".svg", ".bmp", ".tiff")) for f in files)
        has_pdf = any(f.lower().endswith(".pdf") for f in files)

        role_key = "general_reasoning_multimodal"
        primary_capability = "general_reasoning"
        task_type = "general_synthesis"
        rationale = f"General regulatory synthesis and SOP compliance query handled by {self.active_profile} general reasoning model."

        # 1. Visual Inspection & Schematics & OCR (Poster §7, §8, §19)
        if has_img or any(w in p for w in ["scanned", "inspection report", "inspection sheet", "utm reading", "pid diagram", "p&id", "drawing", "ocr", "thickness report", "photo", "image", "handwritten", "handwriting"]):
            role_key = "documents_vision"
            primary_capability = "images_vision" if not any(w in p for w in ["ocr", "handwriting", "read text"]) else "ocr_extraction"
            task_type = "multimodal_inspection"
            rationale = f"Multimodal engineering visual inspection / OCR sheet detected. Routed to {self.active_profile} vision model."

        # 2. Deep Mathematical Calculations & Physics Proofs (Poster §4, §13, §14)
        elif any(w in p for w in ["corrosion rate formula", "remaining life derivation", "derivation", "thermodynamic", "finite element", "asme calculation", "api-510 calculation", "cr mm/year", "half-life proof"]):
            role_key = "deep_reasoning_calc"
            primary_capability = "deep_math_reasoning"
            task_type = "math_derivation"
            rationale = f"Deep mathematical derivation & physics invariant proofs detected. Routed to {self.active_profile} reasoning & calc model."

        # 3. Coding & Sandboxed Math / Telemetry Processing (Poster §4, §5, §12)
        elif any(w in p for w in ["python", "code", "script", "csv", "calculate", "pressure drop", "heat exchanger", "e104", "delta p", "sandbox", "telemetry", "regression", "ols"]):
            role_key = "coding_agent"
            primary_capability = "coding"
            telemetry_task = (
                any(f.lower().endswith((".csv", ".xlsx")) for f in files)
                or any(w in p for w in ["csv", "heat exchanger", "e104", "telemetry", "regression", "ols", "sandbox"])
            )
            if telemetry_task:
                task_type = "coding_sandbox"
                rationale = f"Tabular telemetry / sandboxed engineering computation detected. Routed to {self.active_profile} coding agent."
            else:
                task_type = "general_synthesis"
                rationale = f"General coding request detected. Routed to {self.active_profile} local reasoning model for code generation and explanation."

        # 4. Ultra-Lightweight Classification & CPU Triage
        elif any(w in p for w in ["triage", "ping", "fast check", "quick status", "cpu fallback"]):
            role_key = "cpu_fallback"
            primary_capability = "rapid_classification"
            task_type = "fast_triage"
            rationale = f"Lightweight status check detected. Routed to {self.active_profile} CPU fallback model."

        # 5. PDF & Document Synthesis (Poster §3)
        elif has_pdf or any(w in p for w in ["pdf", "turnaround report", "specification doc", "contract"]):
            role_key = "general_reasoning_multimodal"
            primary_capability = "pdf_analysis"
            task_type = "document_analysis"
            rationale = f"Structured PDF turnaround report / document analysis detected. Routed to {self.active_profile} multimodal model."

        # 6. Summarization & Policy synthesis
        elif any(w in p for w in ["summarize", "summary", "brief", "digest"]):
            role_key = "general_reasoning_multimodal"
            primary_capability = "summarization"
            task_type = "general_synthesis"
            rationale = f"Summarization & SOP compliance synthesis detected. Routed to {self.active_profile} general reasoning model."

        role_info = self.get_role_model(role_key)
        model_tag = role_info.get("ollama_tag", "qwen3.5:9b")
        fallback_tag = role_info.get("fallback_tag", "qwen2.5:1.5b")
        license_type = role_info.get("license", "Apache 2.0")
        model_role_desc = role_info.get("role", "Industrial LLM Role")

        decision = {
            "status": "SUCCESS",
            "active_profile": self.active_profile,
            "role_key": role_key,
            "model_key": role_key,
            "role_description": model_role_desc,
            "model_id": model_tag,
            "model_tag": model_tag,
            "model_alias": f"{model_tag} ({model_role_desc})",
            "fallback_tag": fallback_tag,
            "license": license_type,
            "huggingface_source": role_info.get("huggingface_source", ""),
            "primary_capability": primary_capability,
            "capabilities": [primary_capability, role_key],
            "task_type": task_type,
            "rationale": rationale,
            "hardware_context": {
                "system_ram_gb": self.hardware_state["hardware_detected"]["system_ram_gb"],
                "gpu_vram_gb": self.hardware_state["hardware_detected"]["gpu_vram_gb"]
            },
            "airgap_enforced": True
        }

        # Log routing audit event
        audit_logger.log(
            event="ROUTING_DECISION",
            component="CapabilityRouter",
            details={
                "prompt_snippet": prompt[:120],
                "attached_files": files,
                "active_profile": self.active_profile,
                "role_key": role_key,
                "model_tag": model_tag,
                "rationale": rationale
            },
            status="SUCCESS"
        )

        return decision

router = CapabilityRouter()

if __name__ == "__main__":
    test_prompts = [
        ("Visual Inspection", "Analyze scanned inspection report for vessel V-101", ["v101_scan.png"]),
        ("Deep Math Proof", "Derive corrosion rate formula and prove API-510 half-life interval theorem", []),
        ("Python Sandbox", "Run Python script to calculate heat exchanger E-104 delta P across tube bundle", ["telemetry.csv"]),
        ("PDF Analysis", "Extract inspection tables from annual turnaround memo", ["report.pdf"]),
        ("SOP Synthesis", "Summarize OISD-STD-105 work permit safety requirements for hot work", []),
        ("Fast Triage", "Quick status check on refinery sensor health", [])
    ]

    print("=" * 80)
    print(f"CAPABILITY ROUTER DEMONSTRATION (Active Profile: {router.active_profile})")
    print("=" * 80)
    for name, p, att in test_prompts:
        res = router.route(p, att)
        print(f"\n[Test: {name}]")
        print(f"  • Prompt     : '{p}'")
        print(f"  • Files      : {att}")
        print(f"  • Target Role: {res['role_key']}")
        print(f"  • Model Tag  : {res['model_tag']} [{res['license']}]")
        print(f"  • Rationale  : {res['rationale']}")
    print("\n" + "=" * 80)
