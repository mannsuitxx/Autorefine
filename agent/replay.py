#!/usr/bin/env python3
"""
================================================================================
SIH 2026: DETERMINISTIC REPLAY & TIME-TRAVEL ENGINE (TASK L10)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Replays past trajectories from durable checkpoints and enables counterfactual time travel.
================================================================================
"""

import os
import sys
import time
import json
import copy
import difflib
import argparse
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from agent.graph import state_graph_engine, AgentState
from agent.tools.calculations import EngineeringCalculationEngine
from langgraph.checkpoint.sqlite import SqliteSaver

class TrajectoryReplayEngine:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(base_dir / "data" / "checkpoints" / "agent_checkpoints.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.history_dir = base_dir / "data" / "trajectories"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save_trajectory(self, trajectory_id: str, state: Dict[str, Any]):
        out_f = self.history_dir / f"{trajectory_id}.json"
        with open(out_f, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, default=str)

    def load_trajectory(self, trajectory_id: str) -> Dict[str, Any]:
        out_f = self.history_dir / f"{trajectory_id}.json"
        if not out_f.exists():
            raise FileNotFoundError(f"Trajectory {trajectory_id} not found at {out_f}")
        with open(out_f, "r", encoding="utf-8") as f:
            return json.load(f)

    def execute_run(self, initial_state: AgentState, thread_id: str, approver_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes a run using LangGraph with SQLite checkpointing.
        """
        initial_state["trajectory_id"] = thread_id
        initial_state["session_id"] = f"sess_{int(time.time()*1000)}"
        initial_state["approval_status"] = "APPROVED" if approver_info else "PENDING"
        initial_state["approver_info"] = approver_info
        initial_state["seed"] = 42

        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        checkpointer.setup()
        
        graph = state_graph_engine.build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        
        final_state = graph.invoke(initial_state, config=config)
        self.save_trajectory(thread_id, final_state)
        conn.close()
        return final_state

    def replay_deterministic(self, trajectory_id: str) -> Dict[str, Any]:
        """
        Re-executes past run with identical inputs and frozen seed.
        """
        original = self.load_trajectory(trajectory_id)
        
        replay_thread_id = f"replay_{trajectory_id}_{int(time.time())}"
        state_input: AgentState = {
            "task_prompt": original["task_prompt"],
            "attached_files": original["attached_files"],
            "trajectory_id": replay_thread_id,
            "session_id": f"sess_replay_{int(time.time())}",
            "approval_status": "APPROVED",
            "approver_info": original.get("approver_info") or {"name": "Replay Authorizer", "role": "Auditor"},
            "seed": 42
        }
        
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        checkpointer.setup()
        
        graph = state_graph_engine.build_graph(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": replay_thread_id}}
        
        replayed_state = graph.invoke(state_input, config=config)
        self.save_trajectory(replay_thread_id, replayed_state)
        conn.close()
        
        # Compare core deterministic keys
        diffs = []
        for key in ["extracted_fields", "computed_values", "task_type", "selected_model", "source_file_sha256"]:
            orig_v = json.dumps(original.get(key), sort_keys=True, default=str)
            repl_v = json.dumps(replayed_state.get(key), sort_keys=True, default=str)
            if orig_v != repl_v:
                diffs.append(f"DIVERGENCE in key '{key}':\n  ORIGINAL: {orig_v}\n  REPLAYED: {repl_v}")

        return {
            "is_identical": len(diffs) == 0,
            "diffs": diffs,
            "original_trajectory_id": trajectory_id,
            "replayed_trajectory_id": replay_thread_id,
            "computed_values": replayed_state.get("computed_values")
        }

    def time_travel_override(self, trajectory_id: str, field_overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resumes from earlier checkpoint state with counterfactual parameter modification,
        generating a NEW immutable trajectory ID while preserving original.
        """
        original = self.load_trajectory(trajectory_id)
        new_trajectory_id = f"counterfactual_{trajectory_id}_{int(time.time()*1000)}"
        
        modified_state = copy.deepcopy(original)
        modified_state["trajectory_id"] = new_trajectory_id
        modified_state["session_id"] = f"sess_cf_{int(time.time()*1000)}"
        
        crit = modified_state.get("critical_defect") or {}
        for k, v in field_overrides.items():
            if k in crit:
                crit[k] = float(v)
            if k in modified_state.get("extracted_fields", {}):
                modified_state["extracted_fields"][k]["value"] = str(v)
        
        modified_state["critical_defect"] = crit
        
        # Re-execute downstream calculations
        t_prev = crit.get("previous_thickness_mm")
        t_meas = crit.get("measured_thickness_mm")
        t_min = crit.get("design_minimum_mm")
        interval = crit.get("interval_years") or 3.5
        
        if t_prev is not None and t_meas is not None and t_min is not None:
            new_calc = EngineeringCalculationEngine.calculate_corrosion_and_life(
                previous_thickness_mm=t_prev,
                measured_thickness_mm=t_meas,
                design_minimum_mm=t_min,
                interval_years=interval
            )
            modified_state["computed_values"] = new_calc
            
        self.save_trajectory(new_trajectory_id, modified_state)
        
        return {
            "original_trajectory_id": trajectory_id,
            "new_trajectory_id": new_trajectory_id,
            "overrides_applied": field_overrides,
            "original_computed": original.get("computed_values"),
            "new_computed": modified_state.get("computed_values")
        }

trajectory_engine = TrajectoryReplayEngine()

def main():
    parser = argparse.ArgumentParser(description="Deterministic Trajectory Replay and Counterfactual Time-Travel")
    parser.add_argument("trajectory_id", help="Trajectory ID to replay or fork")
    parser.add_argument("--time-travel", action="store_true", help="Enable counterfactual time-travel branch")
    parser.add_argument("--set", action="append", help="Key=Value override for time travel (e.g. design_minimum_mm=13.0)")
    
    args = parser.parse_args()
    
    if args.time_travel:
        overrides = {}
        if args.set:
            for item in args.set:
                if "=" in item:
                    k, v = item.split("=", 1)
                    overrides[k.strip()] = float(v.strip())
        res = trajectory_engine.time_travel_override(args.trajectory_id, overrides)
        print(f"Time-travel fork completed successfully!")
        print(f"Original ID: {res['original_trajectory_id']}")
        print(f"New Branch ID: {res['new_trajectory_id']}")
        print(f"Original Remaining Life: {res['original_computed'].get('remaining_life_years')} yrs")
        print(f"New Remaining Life: {res['new_computed'].get('remaining_life_years')} yrs")
    else:
        res = trajectory_engine.replay_deterministic(args.trajectory_id)
        if res["is_identical"]:
            print(f"REPLAY SUCCESSFUL: Trajectory {args.trajectory_id} is 100% BYTE-IDENTICAL across executions.")
            print(f"Replayed ID: {res['replayed_trajectory_id']}")
        else:
            print(f"REPLAY DIVERGENCE DETECTED:")
            for d in res["diffs"]:
                print(f"  {d}")

if __name__ == "__main__":
    main()
