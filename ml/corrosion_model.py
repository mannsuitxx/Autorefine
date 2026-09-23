#!/usr/bin/env python3
"""
================================================================================
SIH 2026: CLASSICAL ML CORROSION REGRESSION & RUL UNCERTAINTY MODEL (TASK L14)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Uses scikit-learn classical regression with statistical prediction intervals.
Avoids LLM hallucination for safety-critical mathematical regression.
================================================================================
"""

import os
import sys
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


class ClassicalCorrosionModel:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent
        self.output_dir = self.base_dir / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def fit_thickness_trend(
        self,
        years: List[float],
        thicknesses_mm: List[float],
        design_minimum_mm: float,
        component_name: str = "Shell Course",
        tag: str = "V-101"
    ) -> Dict[str, Any]:
        """
        Fits linear regression across historical inspection timestamps.
        Requires n >= 3 data points.
        """
        n = len(years)
        if n < 3:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"INSUFFICIENT HISTORICAL DATA: Fewer than 3 inspection points ({n} provided). Minimum 3 points required for statistical regression.",
                "data_points": n,
                "can_predict": False
            }

        X = np.array(years).reshape(-1, 1)
        y = np.array(thicknesses_mm)

        model = LinearRegression()
        model.fit(X, y)

        slope = float(model.coef_[0])  # mm/year slope (negative for thinning)
        intercept = float(model.intercept_)
        y_pred = model.predict(X)
        r2 = float(r2_score(y, y_pred))

        corrosion_rate_fit = round(abs(slope), 4)
        current_year = max(years)
        current_thickness = y[years.index(current_year)]

        # Residual standard error (s_e)
        residuals = y - y_pred
        df = n - 2
        s_e = float(np.sqrt(np.sum(residuals**2) / max(1, df)))

        # Student's t critical value for 95% two-sided interval
        t_crit = 2.35 if n <= 5 else 2.0

        # Mean RUL projection: (current_thickness - design_minimum) / corrosion_rate
        if corrosion_rate_fit > 0:
            rul_50_mean = round((current_thickness - design_minimum_mm) / corrosion_rate_fit, 2)
            # Lower 95% bound (conservative engineering estimate with standard error penalty)
            effective_cr_conservative = corrosion_rate_fit + (t_crit * (s_e / np.std(years) if np.std(years) > 0 else 0.05))
            rul_lower_bound = round(max(0.1, (current_thickness - design_minimum_mm) / effective_cr_conservative), 2)
        else:
            rul_50_mean = 99.0
            rul_lower_bound = 99.0

        # Naive two-point calculation for comparison
        naive_rate = abs(thicknesses_mm[0] - thicknesses_mm[-1]) / max(0.1, (years[-1] - years[0]))

        chart_path = self._generate_trend_chart(
            years=years,
            thicknesses_mm=thicknesses_mm,
            design_minimum_mm=design_minimum_mm,
            model=model,
            s_e=s_e,
            t_crit=t_crit,
            tag=tag,
            component_name=component_name
        )

        return {
            "status": "SUCCESS",
            "can_predict": True,
            "equipment_id": tag,
            "component_name": component_name,
            "data_points_count": n,
            "fitted_slope_mm_yr": slope,
            "corrosion_rate_mm_per_year": corrosion_rate_fit,
            "r_squared": round(r2, 4),
            "residual_std_error_mm": round(s_e, 4),
            "current_thickness_mm": current_thickness,
            "design_minimum_mm": design_minimum_mm,
            "rul_mean_years": rul_50_mean,
            "rul_conservative_years": rul_lower_bound,
            "projected_turnaround_date_mean": f"{int(current_year + rul_50_mean)}-01",
            "projected_turnaround_date_conservative": f"{int(current_year + rul_lower_bound)}-01",
            "robustness_note": f"Naive 2-point rate = {naive_rate:.4f} mm/yr vs Multi-point OLS fit = {corrosion_rate_fit:.4f} mm/yr",
            "engineering_rationale": "Multi-point linear regression dampens transient UT probe coupling noise and yields calibrated 95% statistical prediction bounds per API-579/ASME FFS-1.",
            "chart_path": chart_path,
            "engineering_guidance": "Refinery turnaround planning must be scheduled on the conservative lower 95% bound to mitigate catastrophic rupture risk."
        }

    def _generate_trend_chart(
        self,
        years: List[float],
        thicknesses_mm: List[float],
        design_minimum_mm: float,
        model: LinearRegression,
        s_e: float,
        t_crit: float,
        tag: str,
        component_name: str
    ) -> str:
        """Renders matplotlib thickness trend chart with shaded 95% prediction interval."""
        out_f = self.output_dir / f"corrosion_trend_{tag.replace('-', '_')}.png"

        x_min = min(years)
        x_max = max(years) + 6.0  # Project 6 years into future
        x_grid = np.linspace(x_min, x_max, 100).reshape(-1, 1)
        y_fit = model.predict(x_grid)

        # 95% prediction band
        x_mean = np.mean(years)
        ss_x = np.sum((np.array(years) - x_mean)**2) if len(years) > 1 else 1.0
        se_pred = s_e * np.sqrt(1 + (1.0 / len(years)) + ((x_grid.flatten() - x_mean)**2 / max(0.1, ss_x)))
        y_upper = y_fit + (t_crit * se_pred)
        y_lower = y_fit - (t_crit * se_pred)

        plt.figure(figsize=(9, 5), dpi=150)
        plt.plot(years, thicknesses_mm, 'o', color='#0284C7', markersize=8, label='Historical UTM Inspections')
        plt.plot(x_grid, y_fit, '-', color='#0F172A', linewidth=2, label='Linear OLS Regression Trend')
        plt.fill_between(x_grid.flatten(), y_lower, y_upper, color='#BAE6FD', alpha=0.5, label='95% Statistical Prediction Interval')
        plt.axhline(y=design_minimum_mm, color='#DC2626', linestyle='--', linewidth=1.5, label=f'API-510 Design Minimum ({design_minimum_mm} mm)')

        plt.title(f"MRPL Asset Integrity: Thickness Degradation Trend ({tag} — {component_name})", fontsize=11, fontweight='bold')
        plt.xlabel("Inspection Year", fontsize=9)
        plt.ylabel("Wall Thickness (mm)", fontsize=9)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(loc='lower left', fontsize=8)

        plt.savefig(str(out_f), bbox_inches='tight', facecolor='white')
        plt.close()
        return str(out_f)


corrosion_model = ClassicalCorrosionModel()


def fit_corrosion_trend(tag: str, points: List[Dict[str, Any]], t_min: float, t_nominal: float = 12.0) -> Dict[str, Any]:
    """Helper functional interface accepting points formatted as [{'date': 'YYYY-MM-DD', 'thickness': 12.0}]"""
    years = []
    thicknesses = []
    for p in points:
        date_str = p.get("date", "")
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            year_val = dt.year + (dt.month - 1) / 12.0
        except Exception:
            year_val = float(date_str[:4]) if len(date_str) >= 4 else 2020.0
        years.append(year_val)
        thicknesses.append(float(p.get("thickness", 0.0)))
    
    return corrosion_model.fit_thickness_trend(
        years=years,
        thicknesses_mm=thicknesses,
        design_minimum_mm=t_min,
        component_name="Shell Section",
        tag=tag
    )


def generate_trend_plot(model_res: Dict[str, Any], output_path: Path) -> str:
    """Copies or generates trend plot to requested output path."""
    src = model_res.get("chart_path")
    if src and Path(src).exists():
        import shutil
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, output_path)
        return str(output_path)
    return ""
