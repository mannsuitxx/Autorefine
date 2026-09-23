#!/usr/bin/env python3
"""
================================================================================
SIH 2026: FLEET-WIDE INTEGRITY RISK RANKING ENGINE (TASK L14)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Computes composite risk ranking across refinery units and exports prioritized worklist.
================================================================================
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


class FleetRiskEngine:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent
        self.output_dir = self.base_dir / "outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_fleet_assets(self) -> List[Dict[str, Any]]:
        """Returns fleet inventory of refinery equipment."""
        return [
            {
                "asset_tag": "V-101",
                "tag": "V-101",
                "name": "Crude Column Reflux Drum",
                "unit": "CDU-1",
                "consequence_class": "HIGH (Toxic/Flammable)",
                "consequence_weight": 5,
                "current_thickness_mm": 13.1,
                "design_minimum_mm": 12.4,
                "rul_conservative_years": 1.45,
                "inspection_interval_status": "OVERDUE (Turnaround Due)",
                "overdue_days": 180
            },
            {
                "asset_tag": "C-101",
                "tag": "C-101",
                "name": "Atmospheric Distillation Tower",
                "unit": "CDU-1",
                "consequence_class": "CRITICAL (Catastrophic Loss)",
                "consequence_weight": 5,
                "current_thickness_mm": 22.4,
                "design_minimum_mm": 18.0,
                "rul_conservative_years": 4.80,
                "inspection_interval_status": "MONITORING",
                "overdue_days": 0
            },
            {
                "asset_tag": "V-205",
                "tag": "V-205",
                "name": "Debutanizer Overhead Accumulator",
                "unit": "CDU-2",
                "consequence_class": "HIGH (LPG/Sour Gas)",
                "consequence_weight": 4,
                "current_thickness_mm": 16.5,
                "design_minimum_mm": 14.0,
                "rul_conservative_years": 2.10,
                "inspection_interval_status": "PLAN_REPAIR",
                "overdue_days": 60
            },
            {
                "asset_tag": "E-104",
                "tag": "E-104",
                "name": "Crude Pre-Heat Exchanger",
                "unit": "CDU-1",
                "consequence_class": "MEDIUM (Thermal Fouling)",
                "consequence_weight": 3,
                "current_thickness_mm": 11.2,
                "design_minimum_mm": 8.0,
                "rul_conservative_years": 6.20,
                "inspection_interval_status": "NORMAL",
                "overdue_days": 0
            },
            {
                "asset_tag": "T-302",
                "tag": "T-302",
                "name": "Kerosene Flash Drum",
                "unit": "HOU",
                "consequence_class": "HIGH (Hydrotreated Middle Distillates)",
                "consequence_weight": 4,
                "current_thickness_mm": 18.0,
                "design_minimum_mm": 15.0,
                "rul_conservative_years": 3.10,
                "inspection_interval_status": "PLAN_INSPECTION",
                "overdue_days": 30
            },
            {
                "asset_tag": "P-204A",
                "tag": "P-204A",
                "name": "CDU Bottoms Residue Charge Pump",
                "unit": "CDU-1",
                "consequence_class": "MEDIUM (High Temperature)",
                "consequence_weight": 3,
                "current_thickness_mm": 14.8,
                "design_minimum_mm": 10.0,
                "rul_conservative_years": 8.50,
                "inspection_interval_status": "NORMAL",
                "overdue_days": 0
            }
        ]

    def rank_fleet(self) -> List[Dict[str, Any]]:
        """
        Computes deterministic composite risk score:
        Risk = (Consequence Weight * 10) + (35 / max(0.8, RUL_conservative)) + (Overdue Bonus)
        """
        assets = self.get_fleet_assets()
        for a in assets:
            rul = a["rul_conservative_years"]
            cw = a["consequence_weight"]
            overdue_bonus = 30.0 if "OVERDUE" in a["inspection_interval_status"] else (15.0 if "PLAN_REPAIR" in a["inspection_interval_status"] else 0.0)
            
            # Risk formula
            thinning_likelihood = min(50.0, 35.0 / max(0.8, rul))
            risk_score = round((cw * 10.0) + thinning_likelihood + overdue_bonus, 2)
            a["composite_risk_score"] = risk_score
            
            if risk_score >= 80.0:
                a["risk_category"] = "CRITICAL (TIER 1)"
            elif risk_score >= 60.0:
                a["risk_category"] = "HIGH (TIER 2)"
            elif risk_score >= 40.0:
                a["risk_category"] = "MEDIUM (TIER 3)"
            else:
                a["risk_category"] = "LOW (ROUTINE)"

        assets.sort(key=lambda x: x["composite_risk_score"], reverse=True)
        for idx, item in enumerate(assets, start=1):
            item["priority_rank"] = idx
        return assets

    def export_worklist_xlsx(self, output_path: str = "outputs/Fleet_Risk_Turnaround_Worklist.xlsx") -> str:
        """Generates formatted Excel worklist for turnaround management."""
        ranked = self.rank_fleet()
        out_f = Path(output_path)
        out_f.parent.mkdir(parents=True, exist_ok=True)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Turnaround Worklist"

        # Headers
        headers = [
            "Priority Rank", "Equipment Tag", "Equipment Name", "Plant Unit",
            "Consequence Class", "Current Thickness (mm)", "Design Min (mm)",
            "Conservative 95% RUL (yrs)", "Overdue (days)", "Inspection Status",
            "Composite Risk Score", "Risk Tier"
        ]
        ws.append(headers)

        header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Add data rows
        for a in ranked:
            ws.append([
                a["priority_rank"], a["asset_tag"], a["name"], a["unit"],
                a["consequence_class"], a["current_thickness_mm"], a["design_minimum_mm"],
                a["rul_conservative_years"], a["overdue_days"], a["inspection_interval_status"],
                a["composite_risk_score"], a["risk_category"]
            ])

        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(str(out_f))
        return str(out_f)


fleet_risk = FleetRiskEngine()


def compute_fleet_risk() -> List[Dict[str, Any]]:
    """Helper function to return ranked fleet assets."""
    return fleet_risk.rank_fleet()


def export_turnaround_worklist_excel(fleet_data: List[Dict[str, Any]], output_path: Path) -> str:
    """Helper function to export fleet data to excel."""
    return fleet_risk.export_worklist_xlsx(str(output_path))
