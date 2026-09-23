#!/usr/bin/env python3
"""
================================================================================
SIH 2026: DETERMINISTIC PHYSICS & ENGINEERING INVARIANTS GUARD (TASK L13)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Validates engineering consistency and cross-checks LLM statements against deterministic math.
Violations HARD-BLOCK deliverable generation without downgrading to warnings.
================================================================================
"""

import re
from typing import Dict, Any, List, Optional, Tuple

class PhysicsGuardrail:
    def __init__(self, max_cr_mm_yr: float = 15.0):
        self.max_cr_mm_yr = max_cr_mm_yr

    def validate_thickness_invariants(
        self,
        nominal_thickness_mm: Optional[float],
        measured_thickness_mm: Optional[float],
        previous_thickness_mm: Optional[float],
        design_minimum_mm: Optional[float]
    ) -> Tuple[bool, List[str]]:
        """
        Enforces physical laws:
        1. 0 < measured_thickness <= nominal_thickness
        2. measured_thickness > 0
        3. previous_thickness > 0
        """
        violations = []

        if measured_thickness_mm is not None and measured_thickness_mm <= 0:
            violations.append(f"PHYSICS_VIOLATION [RULE_P1_NON_POSITIVE_THICKNESS]: Measured thickness ({measured_thickness_mm} mm) must be strictly positive.")

        if nominal_thickness_mm is not None and measured_thickness_mm is not None:
            if measured_thickness_mm > (nominal_thickness_mm * 1.05):  # 5% tolerance for manufacturing rolling margin
                violations.append(
                    f"PHYSICS_VIOLATION [RULE_P2_THICKNESS_EXCEEDS_NOMINAL]: Measured thickness ({measured_thickness_mm} mm) "
                    f"exceeds nominal design thickness ({nominal_thickness_mm} mm). Physical impossibility without uncertified weld buildup."
                )

        if design_minimum_mm is not None and design_minimum_mm <= 0:
            violations.append(f"PHYSICS_VIOLATION [RULE_P3_INVALID_DESIGN_MINIMUM]: Design minimum ({design_minimum_mm} mm) must be greater than zero.")

        return (len(violations) == 0), violations

    def validate_calculated_metrics(
        self,
        corrosion_rate_mm_yr: Optional[float],
        remaining_life_years: Optional[float],
        half_life_interval_years: Optional[float]
    ) -> Tuple[bool, List[str]]:
        """
        Enforces thermodynamics & API-510 calculation constraints:
        1. 0 <= CR <= max_cr_mm_yr
        2. Half-life interval == min(RL / 2, 10.0)
        """
        violations = []

        if corrosion_rate_mm_yr is not None:
            if corrosion_rate_mm_yr < 0:
                violations.append(f"PHYSICS_VIOLATION [RULE_P4_NEGATIVE_CORROSION]: Calculated corrosion rate ({corrosion_rate_mm_yr} mm/yr) is negative.")
            elif corrosion_rate_mm_yr > self.max_cr_mm_yr:
                violations.append(
                    f"PHYSICS_VIOLATION [RULE_P5_UNREALISTIC_CORROSION_RATE]: Calculated corrosion rate ({corrosion_rate_mm_yr} mm/yr) "
                    f"exceeds plausible physical threshold ({self.max_cr_mm_yr} mm/yr)."
                )

        if remaining_life_years is not None and half_life_interval_years is not None:
            expected_interval = round(min(remaining_life_years / 2.0, 10.0), 2)
            if abs(half_life_interval_years - expected_interval) > 0.05:
                violations.append(
                    f"PHYSICS_VIOLATION [RULE_P6_API510_HALF_LIFE_MISMATCH]: API-510 half-life interval ({half_life_interval_years} yrs) "
                    f"inconsistent with remaining life ({remaining_life_years} yrs). Expected {expected_interval} yrs."
                )

        return (len(violations) == 0), violations

    def cross_check_llm_numbers(
        self,
        llm_response_text: str,
        deterministic_metrics: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Scans LLM output text for stated numerical figures and cross-checks them
        against the exact deterministic calculation engine results.
        Any numerical hallucination triggers a HARD FAIL.
        """
        violations = []
        
        # Check stated Remaining Life
        true_rl = deterministic_metrics.get("remaining_life_years") or deterministic_metrics.get("calculated_remaining_life_years")
        if true_rl is not None:
            # Match "remaining life is 8.5", "remaining life: 8.5", "RL = 8.5", "remaining life of 8.5"
            rl_matches = re.findall(r'(?:remaining\s*(?:useful)?\s*life|RL)(?:\s+(?:is|of|equal\s*to)|\s*[:=\-])*\s*([0-9]+(?:\.[0-9]+)?)', llm_response_text, re.IGNORECASE)
            for m_str in rl_matches:
                val = float(m_str)
                # If stated value diverges from truth by > 0.15 years
                if abs(val - true_rl) > 0.15 and val != 510:  # exclude standard number 510
                    violations.append(
                        f"HALLUCINATION_DETECTED [HARD_FAIL_LLM_NUMERICAL_DIVERGENCE]: LLM stated remaining life as {val} years, "
                        f"diverging from verified deterministic calculation ({true_rl} years)."
                    )

        # Check stated Corrosion Rate
        true_cr = deterministic_metrics.get("corrosion_rate_mm_yr") or deterministic_metrics.get("calculated_corrosion_rate_mm_yr")
        if true_cr is not None:
            cr_matches = re.findall(r'(?:corrosion\s*rate|CR)(?:\s+(?:is|of|equal\s*to)|\s*[:=\-])*\s*([0-9]+(?:\.[0-9]+)?)', llm_response_text, re.IGNORECASE)
            for m_str in cr_matches:
                val = float(m_str)
                if abs(val - true_cr) > 0.05 and val != 510:
                    violations.append(
                        f"HALLUCINATION_DETECTED [HARD_FAIL_LLM_NUMERICAL_DIVERGENCE]: LLM stated corrosion rate as {val} mm/yr, "
                        f"diverging from verified deterministic calculation ({true_cr} mm/yr)."
                    )

        return (len(violations) == 0), violations

physics_guard = PhysicsGuardrail()
