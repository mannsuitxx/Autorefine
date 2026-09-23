#!/usr/bin/env python3
"""
================================================================================
SIH 2026: CALIBRATED CONFIDENCE & ABSTENTION ENGINE (TASK L13)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Calibrates extraction, OCR, retrieval, and physics scores.
If confidence falls below threshold, the agent ABSTAINS instead of guessing.
================================================================================
"""

from typing import Dict, Any, List, Optional, Tuple

class CalibratedAbstentionEngine:
    def __init__(self, threshold: float = 0.80):
        self.threshold = threshold

    def evaluate_confidence(
        self,
        extracted_fields: Dict[str, Any],
        critical_component: Optional[Dict[str, Any]],
        ocr_confidence_pct: float = 90.0,
        retrieval_margin: float = 0.90,
        physics_violations: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculates holistic calibrated confidence.
        If essential inputs are missing or physics laws are broken, forces ABSTENTION.
        """
        physics_violations = physics_violations or []
        missing_evidence = []

        # Check required fields
        crit = critical_component or {}
        if not extracted_fields.get("equipment_tag", {}).get("value"):
            missing_evidence.append("Equipment Tag / Asset ID")
        if crit.get("measured_thickness_mm") is None:
            missing_evidence.append("Measured Actual Wall Thickness (t_meas)")
        if crit.get("previous_thickness_mm") is None:
            missing_evidence.append("Prior Inspection Wall Thickness (t_prev)")
        if crit.get("design_minimum_mm") is None:
            missing_evidence.append("Statutory Design Minimum Thickness (t_min / t_req)")

        # Factor weights
        w_ocr = min(1.0, ocr_confidence_pct / 100.0)
        w_field = max(0.0, 1.0 - (len(missing_evidence) * 0.30))
        w_retrieval = min(1.0, retrieval_margin)
        w_physics = 0.0 if len(physics_violations) > 0 else 1.0

        # Weighted aggregate score
        calibrated_score = round(
            (0.25 * w_ocr) +
            (0.35 * w_field) +
            (0.20 * w_retrieval) +
            (0.20 * w_physics),
            3
        )

        should_abstain = (calibrated_score < self.threshold) or (len(missing_evidence) > 0) or (len(physics_violations) > 0)

        abstention_reason = None
        if should_abstain:
            reasons = []
            if missing_evidence:
                reasons.append(f"Missing mandatory engineering inputs: {', '.join(missing_evidence)}")
            if physics_violations:
                reasons.append(f"Physics invariant violations: {'; '.join(physics_violations)}")
            if calibrated_score < self.threshold:
                reasons.append(f"Calibrated confidence score ({calibrated_score}) below acceptable safety threshold ({self.threshold})")
            
            abstention_reason = (
                f"AGENT ABSTENTION: Cannot safely authorize or compute engineering integrity deliverables.\n"
                f"Root Cause: {' | '.join(reasons)}.\n"
                f"Action: Execution halted. Escalating to Senior Inspection Engineer for manual field verification."
            )

        return {
            "calibrated_confidence": calibrated_score,
            "threshold": self.threshold,
            "should_abstain": should_abstain,
            "missing_evidence": missing_evidence,
            "physics_violations": physics_violations,
            "abstention_message": abstention_reason
        }

abstention_engine = CalibratedAbstentionEngine()
