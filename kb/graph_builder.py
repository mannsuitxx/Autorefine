#!/usr/bin/env python3
"""
================================================================================
SIH 2026: EQUIPMENT KNOWLEDGE GRAPH BUILDER (TASK L12)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Constructs relational graph with node/edge provenance from refinery SOPs & inspection findings.
================================================================================
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx

class EquipmentKnowledgeGraphBuilder:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent
        self.kg_dir = self.base_dir / "data" / "knowledge_graph"
        self.kg_dir.mkdir(parents=True, exist_ok=True)
        self.kg_file = self.kg_dir / "equipment_kg.json"
        self.graph = nx.DiGraph()

    def build_default_refinery_graph(self) -> nx.DiGraph:
        """
        Builds deterministic refinery asset integrity knowledge graph with strict provenance.
        """
        G = nx.DiGraph()

        # Helper to add node with provenance
        def add_node(node_id: str, node_type: str, label: str, source_doc: str, source_span: str, attributes: Optional[Dict[str, Any]] = None):
            attrs = attributes or {}
            G.add_node(
                node_id,
                node_type=node_type,
                label=label,
                source_doc=source_doc,
                source_span=source_span,
                **attrs
            )

        # Helper to add edge with provenance
        def add_edge(u: str, v: str, relation: str, source_doc: str, source_span: str):
            G.add_edge(
                u, v,
                relation=relation,
                source_doc=source_doc,
                source_span=source_span
            )

        # ----------------------------------------------------------------------
        # 1. PLANT UNITS
        # ----------------------------------------------------------------------
        add_node("UNIT:CDU-1", "PlantUnit", "Crude Distillation Unit 1 (CDU-1)", "MRPL_P&ID_CDU_101.svg", "Unit boundary CDU-1", {"capacity_bpd": 150000})
        add_node("UNIT:CDU-2", "PlantUnit", "Crude Distillation Unit 2 (CDU-2)", "MRPL_P&ID_CDU_205.svg", "Unit boundary CDU-2", {"capacity_bpd": 180000})
        add_node("UNIT:HOU", "PlantUnit", "Hydrocracker Unit (HOU)", "MRPL_P&ID_HOU_302.svg", "Unit boundary HOU", {"capacity_bpd": 90000})

        # ----------------------------------------------------------------------
        # 2. EQUIPMENT
        # ----------------------------------------------------------------------
        add_node("EQ:V-101", "Equipment", "V-101 Crude Column Reflux Drum", "CDU_V101_Inspection_Turnaround_Report.png", "EQUIPMENT: V-101 (Crude Column Reflux Drum)", {"tag": "V-101", "design_pressure_bar": 18.5})
        add_node("EQ:C-101", "Equipment", "C-101 Atmospheric Fractionation Column", "MRPL_P&ID_CDU_101.svg", "Main crude distillation tower C-101", {"tag": "C-101", "design_pressure_bar": 4.5})
        add_node("EQ:V-205", "Equipment", "V-205 Debutanizer Overhead Accumulator", "V205_Different_Inspection_Report.png", "EQUIPMENT: V.205 (Debutanizer Overhead Accumulator)", {"tag": "V-205", "design_pressure_bar": 12.0})
        add_node("EQ:E-104", "Equipment", "E-104 Crude Pre-Heat Exchanger", "E104_Heat_Exchanger_Operating_Log.csv", "Heat Exchanger E-104 shell & tube", {"tag": "E-104", "shell_design_bar": 25.0})
        add_node("EQ:T-302", "Equipment", "T-302 Kerosene Flash Drum", "Different_Labels_Inspection_Report.png", "Asset ID: 802 / T-302 Kerosene Flash Drum", {"tag": "T-302", "design_pressure_bar": 15.0})

        # Unit -> Equipment CONTAINS edges
        add_edge("UNIT:CDU-1", "EQ:V-101", "CONTAINS", "MRPL_P&ID_CDU_101.svg", "CDU-1 Process Stream contains V-101")
        add_edge("UNIT:CDU-1", "EQ:C-101", "CONTAINS", "MRPL_P&ID_CDU_101.svg", "CDU-1 Process Stream contains C-101")
        add_edge("UNIT:CDU-1", "EQ:E-104", "CONTAINS", "MRPL_P&ID_CDU_101.svg", "CDU-1 Process Stream contains E-104")
        add_edge("UNIT:CDU-2", "EQ:V-205", "CONTAINS", "MRPL_P&ID_CDU_205.svg", "CDU-2 Process Stream contains V-205")
        add_edge("UNIT:HOU", "EQ:T-302", "CONTAINS", "MRPL_P&ID_HOU_302.svg", "HOU Process Stream contains T-302")

        # ----------------------------------------------------------------------
        # 3. COMPONENTS & MATERIALS
        # ----------------------------------------------------------------------
        add_node("COMP:V101_SHELL_C3", "Component", "V-101 Shell Course 3", "CDU_V101_Inspection_Turnaround_Report.png", "Shell Course 3: Nominal 14.6 mm", {"nominal_mm": 14.6, "min_req_mm": 12.4})
        add_node("COMP:V101_HEAD_TOP", "Component", "V-101 Top Head", "CDU_V101_Inspection_Turnaround_Report.png", "Head Top: Nominal 14.6 mm", {"nominal_mm": 14.6, "min_req_mm": 12.0})
        add_node("COMP:C101_FLASH_ZONE", "Component", "C-101 Flash Zone Section", "MRPL_SOP_042_Hot_Work_Protocol.md", "Section 4.1: Column Flash Zone Tray 1-4", {"nominal_mm": 25.0, "min_req_mm": 18.0})
        add_node("COMP:V205_SHELL_C1", "Component", "V-205 Shell Course 1", "V205_Different_Inspection_Report.png", "Shell Course 1: Nominal 22.0 mm", {"nominal_mm": 22.0, "min_req_mm": 14.0})

        add_node("MAT:CS_SA516", "Material", "SA-516 Gr. 70 Carbon Steel", "API_510_Pressure_Vessel_Inspection_Code.md", "Material Spec SA-516 Gr 70", {"yield_mpa": 260, "tensile_mpa": 485})
        add_node("MAT:SS_316L", "Material", "316L Stainless Steel Cladding", "API_510_Pressure_Vessel_Inspection_Code.md", "Corrosion Resistant Overlay Alloy 316L", {"moly_pct": 2.5})

        add_edge("EQ:V-101", "COMP:V101_SHELL_C3", "CONTAINS", "CDU_V101_Inspection_Turnaround_Report.png", "V-101 contains Shell Course 3")
        add_edge("EQ:V-101", "COMP:V101_HEAD_TOP", "CONTAINS", "CDU_V101_Inspection_Turnaround_Report.png", "V-101 contains Top Head")
        add_edge("EQ:C-101", "COMP:C101_FLASH_ZONE", "CONTAINS", "MRPL_P&ID_CDU_101.svg", "C-101 contains Flash Zone Section")
        add_edge("EQ:V-205", "COMP:V205_SHELL_C1", "CONTAINS", "V205_Different_Inspection_Report.png", "V-205 contains Shell Course 1")

        add_edge("COMP:V101_SHELL_C3", "MAT:CS_SA516", "MADE_OF", "CDU_V101_Inspection_Turnaround_Report.png", "V-101 Shell 3 constructed from SA-516 Gr 70")
        add_edge("COMP:C101_FLASH_ZONE", "MAT:CS_SA516", "MADE_OF", "MRPL_SOP_042_Hot_Work_Protocol.md", "C-101 Flash zone carbon steel substrate")
        add_edge("COMP:V205_SHELL_C1", "MAT:CS_SA516", "MADE_OF", "V205_Different_Inspection_Report.png", "V-205 Shell 1 carbon steel")

        # ----------------------------------------------------------------------
        # 4. DAMAGE MECHANISMS & SUSCEPTIBILITY
        # ----------------------------------------------------------------------
        add_node("DM:NAPHTHENIC_ACID", "DamageMechanism", "Naphthenic Acid Corrosion (API 571 §3.46)", "API_510_Pressure_Vessel_Inspection_Code.md", "API 571 Section 3.46: Naphthenic Acid Corrosion in Heavy Crude", {"api571_ref": "3.46", "temp_range_c": "220-400 C"})
        add_node("DM:H2S_PITTING", "DamageMechanism", "Wet H2S / Sour Water Pitting (API 571 §3.58)", "API_510_Pressure_Vessel_Inspection_Code.md", "API 571 Section 3.58: Wet H2S Damage and Pitting in Sour Services", {"api571_ref": "3.58"})

        add_edge("MAT:CS_SA516", "DM:NAPHTHENIC_ACID", "SUSCEPTIBLE_TO", "API_510_Pressure_Vessel_Inspection_Code.md", "Unclad carbon steel SA-516 is highly susceptible to high-TAN crude naphthenic acid attack above 230 C")
        add_edge("MAT:CS_SA516", "DM:H2S_PITTING", "SUSCEPTIBLE_TO", "API_510_Pressure_Vessel_Inspection_Code.md", "Carbon steel in wet H2S sour condensate service susceptible to local pitting")

        # ----------------------------------------------------------------------
        # 5. DEFECTS & OBSERVATIONS
        # ----------------------------------------------------------------------
        add_node("DEF:V101_SHELL3_THINNING", "Defect", "Accelerated Wall Thinning on V-101 Course 3 (13.1 mm)", "CDU_V101_Inspection_Turnaround_Report.png", "Course 3: Actual measured 13.1 mm (Remaining life 1.63 yrs)", {"measured_mm": 13.1, "rate_mm_yr": 0.429})
        add_node("DEF:C101_FLASH_GROOVING", "Defect", "Localized Flow-Induced Grooving on C-101 Tray Support", "MRPL_SOP_042_Hot_Work_Protocol.md", "Inspection Log 2025: Flow grooving near nozzle N3", {"measured_mm": 18.2})

        add_edge("DEF:V101_SHELL3_THINNING", "COMP:V101_SHELL_C3", "OBSERVED_ON", "CDU_V101_Inspection_Turnaround_Report.png", "Defect observed on Shell Course 3 during 2026 Turnaround")
        add_edge("DEF:V101_SHELL3_THINNING", "DM:NAPHTHENIC_ACID", "CAUSED_BY", "CDU_V101_Inspection_Turnaround_Report.png", "Metallurgical finding: high-temperature organic acid thinning consistent with Naphthenic Acid Corrosion")
        add_edge("DEF:C101_FLASH_GROOVING", "COMP:C101_FLASH_ZONE", "OBSERVED_ON", "MRPL_SOP_042_Hot_Work_Protocol.md", "Grooving observed in column flash section")
        add_edge("DEF:C101_FLASH_GROOVING", "DM:NAPHTHENIC_ACID", "CAUSED_BY", "MRPL_SOP_042_Hot_Work_Protocol.md", "High TAN crude wash velocity corrosion")

        # ----------------------------------------------------------------------
        # 6. RECOMMENDED ACTIONS & STANDARD CLAUSES
        # ----------------------------------------------------------------------
        add_node("ACT:WELD_OVERLAY_316L", "RecommendedAction", "Internal 316L Weld Overlay Restoration", "API_510_Pressure_Vessel_Inspection_Code.md", "API 510 §7.1.1: Restoring wall thickness with weld metal buildup or cladding overlay", {"procedure_code": "MRPL-WPS-316L-04"})
        add_node("ACT:HOT_WORK_PERMIT", "RecommendedAction", "Execution under Class-A Hot Work Safety Permit", "OISD_STD_105_Work_Permit_System.md", "OISD-STD-105 §6.2: Pre-work gas testing, LEL continuous monitoring, fire watch", {"permit_class": "Class A Hot Work"})

        add_node("STD:API510_SEC7", "StandardClause", "API-510 §7.1.1 (Pressure Vessel Repairs & Alterations)", "API_510_Pressure_Vessel_Inspection_Code.md", "API 510 Section 7.1.1 specifies approved permanent repairs for thinned pressure boundaries", {"standard": "API-510", "section": "7.1.1"})
        add_node("STD:OISD105_SEC6", "StandardClause", "OISD-STD-105 §6.2 (Permit-to-Work Hot Work Authorization)", "OISD_STD_105_Work_Permit_System.md", "OISD-STD-105 Section 6.2 mandates combustible gas testing < 1% LEL before welding on hydrocarbon vessels", {"standard": "OISD-STD-105", "section": "6.2"})

        add_edge("DEF:V101_SHELL3_THINNING", "ACT:WELD_OVERLAY_316L", "MITIGATED_BY", "CDU_V101_Inspection_Turnaround_Report.png", "Corrosion mitigation recommendation: Weld overlay repair")
        add_edge("ACT:WELD_OVERLAY_316L", "STD:API510_SEC7", "GOVERNED_BY", "API_510_Pressure_Vessel_Inspection_Code.md", "Weld metal restoration is governed by API-510 §7.1.1 design requirements")
        add_edge("ACT:WELD_OVERLAY_316L", "ACT:HOT_WORK_PERMIT", "REQUIRES", "OISD_STD_105_Work_Permit_System.md", "Welding repair inside confined refinery vessel requires active Class-A Hot Work Permit")
        add_edge("ACT:HOT_WORK_PERMIT", "STD:OISD105_SEC6", "GOVERNED_BY", "OISD_STD_105_Work_Permit_System.md", "Hot work execution is strictly governed by OISD-STD-105 §6.2 mandatory safety controls")

        self.graph = G
        self.save_graph()
        return G

    def save_graph(self):
        """Serializes graph to disk with node and edge attributes."""
        data = nx.node_link_data(self.graph)
        with open(self.kg_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_graph(self) -> nx.DiGraph:
        """Loads graph from disk if present, else builds from default."""
        if self.kg_file.exists():
            with open(self.kg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)
            return self.graph
        return self.build_default_refinery_graph()

# Global Knowledge Graph Builder Singleton
kg_builder = EquipmentKnowledgeGraphBuilder()

if __name__ == "__main__":
    G = kg_builder.build_default_refinery_graph()
    print(f"Refinery Knowledge Graph constructed with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    print(f"Persisted to {kg_builder.kg_file}")
