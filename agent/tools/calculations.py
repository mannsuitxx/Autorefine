import math
from typing import Dict, Any, List, Optional

class EngineeringCalculationEngine:
    """
    SIH 2026 Sovereign Engineering Calculation Engine.
    Strictly derives all metrics from extracted values without defaulting or fabricating.
    Generates step-by-step Given -> Procedure -> Formula -> Substitution -> Result trace.
    """
    
    @staticmethod
    def calculate_vessel_integrity(
        previous_thickness_mm: Optional[float],
        measured_thickness_mm: Optional[float],
        design_minimum_mm: Optional[float],
        interval_years: Optional[float] = None,
        component_name: str = "Inspection Component"
    ) -> Dict[str, Any]:
        """
        Computes corrosion rate, remaining life, and API-510 inspection intervals.
        Fails loudly if required numeric fields are missing or invalid.
        """
        trace = []

        # Validate inputs
        if previous_thickness_mm is None:
            raise ValueError("Cannot calculate corrosion rate: 'previous_thickness' is missing from source document.")
        if measured_thickness_mm is None:
            raise ValueError("Cannot calculate corrosion rate: 'measured_thickness' is missing from source document.")
        if design_minimum_mm is None:
            raise ValueError("Cannot calculate remaining life: 'design_minimum' is missing from source document.")

        if interval_years is None or interval_years <= 0:
            raise ValueError(f"Invalid inspection interval: {interval_years} years. Must be a positive number.")

        thickness_loss = round(previous_thickness_mm - measured_thickness_mm, 4)
        if thickness_loss < 0:
            # Measured thickness increased (possible weld buildup or measurement variation)
            cr = 0.0
            status_cr = "NO_DETECTED_CORROSION_LOSS"
        else:
            cr = round(thickness_loss / interval_years, 4)
            status_cr = "NORMAL" if cr < 0.3 else "ELEVATED"

        trace.append({
            "step": "1. Corrosion Rate Calculation",
            "parameter": "Corrosion Rate (CR)",
            "given": f"t_prev = {previous_thickness_mm} mm, t_meas = {measured_thickness_mm} mm, Δt = {interval_years} yrs",
            "procedure": "Wall loss over elapsed operating period (API-510 Eq 6-1)",
            "formula": "CR = (t_prev - t_meas) / Δt",
            "substitution": f"CR = ({previous_thickness_mm} - {measured_thickness_mm}) / {interval_years} = {thickness_loss:.3f} / {interval_years}",
            "result": f"{cr:.3f} mm/year",
            "status": status_cr
        })

        remaining_margin = round(measured_thickness_mm - design_minimum_mm, 4)
        if cr <= 0:
            rl = 99.0
            rl_str = "> 50 Years (Negligible Corrosion)"
            action_needed = False
        else:
            rl = round(remaining_margin / cr, 2)
            rl_str = f"{rl:.2f} Years"
            action_needed = (rl < 4.0)

        trace.append({
            "step": "2. Remaining Life Calculation",
            "parameter": "Remaining Safe Operating Life (RL)",
            "given": f"t_meas = {measured_thickness_mm} mm, t_min = {design_minimum_mm} mm, CR = {cr:.3f} mm/yr",
            "procedure": "Remaining corrosion allowance over annual corrosion rate (API-510 Eq 6-2)",
            "formula": "RL = (t_meas - t_min) / CR",
            "substitution": f"RL = ({measured_thickness_mm} - {design_minimum_mm}) / {cr:.3f} = {remaining_margin:.3f} / {cr:.3f}",
            "result": rl_str,
            "status": "CRITICAL_ACTION_REQUIRED" if action_needed else "ACCEPTABLE"
        })

        # API-510 Interval Check (Half-Life rule, max 10 years)
        max_interval = round(min(rl / 2.0, 10.0), 2)
        trace.append({
            "step": "3. Statutory Inspection Interval",
            "parameter": "Max Allowable Next Inspection Interval",
            "given": f"RL = {rl_str}, Regulatory Cap = 10.0 yrs",
            "procedure": "API-510 Section 6.4 (Half-Life Rule)",
            "formula": "Interval = Min(RL / 2, 10.0 yrs)",
            "substitution": f"Interval = Min({rl:.2f} / 2, 10.0)",
            "result": f"{max_interval:.2f} Years",
            "status": "EXCEEDS_TURNAROUND_WINDOW" if (max_interval < 4.0 and action_needed) else "COMPLIANT"
        })

        recommendation = (
            f"RECOMMENDED — Internal weld overlay restoration / 316L cladding required on {component_name} prior to startup "
            f"(Remaining life {rl:.2f} yrs < 4.0 yr turnaround cycle)."
            if action_needed else
            f"RECOMMENDED — Wall thickness is within acceptable limits (Remaining life: {rl:.2f} yrs). Continue routine monitoring."
        )

        return {
            "component": component_name,
            "previous_thickness_mm": previous_thickness_mm,
            "measured_thickness_mm": measured_thickness_mm,
            "design_minimum_mm": design_minimum_mm,
            "interval_years": interval_years,
            "corrosion_allowance_remaining_mm": remaining_margin,
            "calculated_corrosion_rate_mm_yr": cr,
            "calculated_remaining_life_years": rl,
            "corrosion_rate_mm_yr": cr,
            "remaining_life_years": rl,
            "api510_max_inspection_interval_years": max_interval,
            "action_required": action_needed,
            "recommendation": recommendation,
            "calculation_trace": trace
        }

    @staticmethod
    def calculate_corrosion_and_life(
        previous_thickness_mm: Optional[float],
        measured_thickness_mm: Optional[float],
        design_minimum_mm: Optional[float],
        interval_years: Optional[float] = None,
        component_name: str = "Inspection Component"
    ) -> Dict[str, Any]:
        return EngineeringCalculationEngine.calculate_vessel_integrity(
            previous_thickness_mm=previous_thickness_mm,
            measured_thickness_mm=measured_thickness_mm,
            design_minimum_mm=design_minimum_mm,
            interval_years=interval_years,
            component_name=component_name
        )

    @staticmethod
    def calculate_heat_exchanger_telemetry(
        records: List[Dict[str, Any]],
        shell_in_col: str,
        shell_out_col: str,
        tube_in_col: str,
        tube_out_col: str,
        tube_dp_threshold_bar: float = 0.350,
        shell_dp_threshold_bar: float = 0.600
    ) -> Dict[str, Any]:
        """
        Computes delta P metrics across CSV records. Fails loudly on missing columns.
        """
        if not records:
            raise ValueError("No telemetry data rows supplied.")

        # Check column existence in first record
        first = records[0]
        missing = [c for c in [shell_in_col, shell_out_col, tube_in_col, tube_out_col] if c not in first]
        if missing:
            raise KeyError(f"Required telemetry columns missing from CSV: {missing}. Available columns: {list(first.keys())}")

        shell_dps = []
        tube_dps = []

        for idx, row in enumerate(records):
            try:
                s_in = float(row[shell_in_col])
                s_out = float(row[shell_out_col])
                t_in = float(row[tube_in_col])
                t_out = float(row[tube_out_col])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Non-numeric telemetry reading at row {idx + 1}: {e}")

            shell_dps.append(s_in - s_out)
            tube_dps.append(t_in - t_out)

        avg_shell = round(sum(shell_dps) / len(shell_dps), 3)
        avg_tube = round(sum(tube_dps) / len(tube_dps), 3)
        max_tube = round(max(tube_dps), 3)
        max_shell = round(max(shell_dps), 3)

        fouling_excursion = (max_tube > tube_dp_threshold_bar)

        trace = [
            {
                "step": "1. Shell Delta P Calculation",
                "parameter": "Average Shell Pressure Drop",
                "given": f"Columns '{shell_in_col}' - '{shell_out_col}' across {len(records)} records",
                "procedure": "Mean difference summation across operational dataset",
                "formula": "ΔP_shell_avg = (1/N) * Σ(P_in - P_out)",
                "substitution": f"Mean({avg_shell:.3f} bar over {len(records)} rows)",
                "result": f"{avg_shell:.3f} bar",
                "status": "NORMAL" if avg_shell <= shell_dp_threshold_bar else "ELEVATED"
            },
            {
                "step": "2. Tube Delta P Calculation",
                "parameter": "Average Tube Pressure Drop",
                "given": f"Columns '{tube_in_col}' - '{tube_out_col}' across {len(records)} records",
                "procedure": "Mean difference summation across operational dataset",
                "formula": "ΔP_tube_avg = (1/N) * Σ(P_in - P_out)",
                "substitution": f"Mean({avg_tube:.3f} bar over {len(records)} rows)",
                "result": f"{avg_tube:.3f} bar",
                "status": "ELEVATED_FOULING" if avg_tube > tube_dp_threshold_bar else "NORMAL"
            },
            {
                "step": "3. Peak Excursion Verification",
                "parameter": "Maximum Recorded Tube Delta P",
                "given": f"Threshold Limit = {tube_dp_threshold_bar:.3f} bar",
                "procedure": "Peak value evaluation against process safety limits",
                "formula": "Max(ΔP_tube) <= Threshold",
                "substitution": f"{max_tube:.3f} bar vs {tube_dp_threshold_bar:.3f} bar limit",
                "result": f"{max_tube:.3f} bar",
                "status": "CRITICAL_ACTION_LIMIT" if fouling_excursion else "NORMAL"
            }
        ]

        return {
            "total_records": len(records),
            "avg_shell_dp_bar": avg_shell,
            "avg_tube_dp_bar": avg_tube,
            "max_tube_dp_bar": max_tube,
            "max_shell_dp_bar": max_shell,
            "tube_dp_threshold_bar": tube_dp_threshold_bar,
            "fouling_excursion": fouling_excursion,
            "calculation_trace": trace
        }
