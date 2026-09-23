#!/usr/bin/env python3
"""
================================================================================
SIH 2026: HARDWARE DETECTION & ADAPTIVE PROFILE SELECTOR (TASK L20)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Detects actual system RAM and GPU VRAM without hardcoded assumptions.
Selects between STANDARD (laptop-safe) and HIGH_RESOURCE (venue server) profiles.
================================================================================
"""

import os
import sys
import json
import yaml
import shutil
import psutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

CONFIG_PATH = base_dir / "config" / "model_registry.yaml"
if not CONFIG_PATH.exists():
    CONFIG_PATH = base_dir / "model_registry.yaml"

class HardwareDetector:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_system_ram_gb(self) -> float:
        """Returns total physical RAM in GB."""
        mem = psutil.virtual_memory()
        return round(mem.total / (1024 ** 3), 2)

    def get_gpu_vram_gb(self) -> Tuple[float, str]:
        """
        Queries nvidia-smi or rocm-smi for dedicated GPU VRAM.
        Returns (vram_gb, gpu_name).
        """
        # Check nvidia-smi
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                out = subprocess.check_output(
                    [nvidia_smi, "--query-gpu=name,memory.total", "--format=csv,nounits,noheader"],
                    stderr=subprocess.DEVNULL
                ).decode("utf-8").strip()
                if out:
                    lines = out.splitlines()
                    parts = lines[0].split(",")
                    gpu_name = parts[0].strip()
                    vram_mb = float(parts[1].strip())
                    return round(vram_mb / 1024.0, 2), gpu_name
            except Exception:
                pass

        # Check rocm-smi
        rocm_smi = shutil.which("rocm-smi")
        if rocm_smi:
            try:
                out = subprocess.check_output([rocm_smi, "--showmeminfo", "vram"], stderr=subprocess.DEVNULL).decode("utf-8")
                # Parse ROCm output if available
                return 0.0, "AMD ROCm GPU (Generic)"
            except Exception:
                pass

        return 0.0, "No Discrete GPU Detected (CPU / Integrated Graphics)"

    def get_gpu_telemetry(self) -> Dict[str, Any]:
        """Return live total/used VRAM and utilization without simulating values."""
        nvidia_smi = shutil.which("nvidia-smi")
        if nvidia_smi:
            try:
                out = subprocess.check_output(
                    [nvidia_smi, "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                     "--format=csv,nounits,noheader"],
                    stderr=subprocess.DEVNULL
                ).decode("utf-8").strip()
                if out:
                    name, total, used, utilization = [part.strip() for part in out.splitlines()[0].split(",")]
                    total_mb = float(total)
                    used_mb = float(used)
                    return {
                        "gpu_device": name,
                        "vram_total_gb": round(total_mb / 1024.0, 2),
                        "vram_used_gb": round(used_mb / 1024.0, 2),
                        "vram_free_gb": round(max(total_mb - used_mb, 0) / 1024.0, 2),
                        "gpu_utilization_percent": float(utilization),
                        "telemetry_source": "nvidia-smi",
                    }
            except (OSError, ValueError, IndexError, subprocess.SubprocessError):
                pass
        return {
            "gpu_device": "No Discrete GPU Detected (CPU / Integrated Graphics)",
            "vram_total_gb": 0.0,
            "vram_used_gb": 0.0,
            "vram_free_gb": 0.0,
            "gpu_utilization_percent": 0.0,
            "telemetry_source": "unavailable",
        }

    def detect_and_select_profile(
        self,
        simulate_ram: Optional[float] = None,
        simulate_vram: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluates hardware metrics against registry profiles.
        Returns selected profile name, detected hardware specs, and assigned model mapping.
        """
        is_simulated = simulate_ram is not None or simulate_vram is not None
        
        real_ram = self.get_system_ram_gb()
        real_vram, gpu_name = self.get_gpu_vram_gb()
        gpu_telemetry = self.get_gpu_telemetry()

        active_ram = float(simulate_ram) if simulate_ram is not None else real_ram
        active_vram = float(simulate_vram) if simulate_vram is not None else real_vram

        # Profile Selection Rules:
        # HIGH_RESOURCE activates when VRAM >= 8.0 GB and RAM >= 24.0 GB
        # STANDARD activates when VRAM < 8.0 GB or RAM < 24.0 GB
        if active_vram >= 8.0 and active_ram >= 24.0:
            selected_profile = "HIGH_RESOURCE"
            reasoning = (
                f"Selected HIGH_RESOURCE: Detected {active_ram}GB RAM (>=24GB threshold) "
                f"and {active_vram}GB VRAM (>=8GB threshold). Hardware supports 24B class models."
            )
        else:
            selected_profile = "STANDARD"
            if active_vram < 8.0 and active_ram < 24.0:
                reason = f"both VRAM ({active_vram}GB < 8GB) and RAM ({active_ram}GB < 24GB)"
            elif active_vram < 8.0:
                reason = f"VRAM ({active_vram}GB < 8GB threshold)"
            else:
                reason = f"RAM ({active_ram}GB < 24GB threshold)"
            reasoning = (
                f"Selected STANDARD: Hardware constrained by {reason}. "
                f"Activated laptop-safe 7B-9B models to prevent RAM thrashing and OOM."
            )

        profiles_data = self.config.get("profiles", {})
        profile_config = profiles_data.get(selected_profile, {})
        models = profile_config.get("models", {})

        return {
            "status": "SUCCESS",
            "active_profile": selected_profile,
            "is_simulated": is_simulated,
            "reasoning": reasoning,
            "hardware_detected": {
                "system_ram_gb": active_ram,
                "real_ram_gb": real_ram,
                "gpu_vram_gb": active_vram,
                "real_vram_gb": real_vram,
                "gpu_vram_used_gb": 0.0 if is_simulated else gpu_telemetry["vram_used_gb"],
                "gpu_vram_free_gb": active_vram if is_simulated else gpu_telemetry["vram_free_gb"],
                "gpu_utilization_percent": 0.0 if is_simulated else gpu_telemetry["gpu_utilization_percent"],
                "gpu_telemetry_source": "simulated" if is_simulated else gpu_telemetry["telemetry_source"],
                "gpu_device": gpu_name if not is_simulated else f"Simulated Accelerator ({active_vram}GB VRAM)",
                "cpu_cores": psutil.cpu_count(logical=True),
                "cpu_physical_cores": psutil.cpu_count(logical=False)
            },
            "profile_description": profile_config.get("description", ""),
            "models": models
        }

hardware_detector = HardwareDetector()

def detect(simulate_ram: Optional[float] = None, simulate_vram: Optional[float] = None) -> Dict[str, Any]:
    return hardware_detector.detect_and_select_profile(simulate_ram=simulate_ram, simulate_vram=simulate_vram)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MRPL Hardware Detection & Profile Selector")
    parser.add_argument("--simulate-ram", type=float, default=None, help="Simulate RAM in GB")
    parser.add_argument("--simulate-vram", type=float, default=None, help="Simulate VRAM in GB")
    args = parser.parse_args()

    result = detect(simulate_ram=args.simulate_ram, simulate_vram=args.simulate_vram)
    print("=" * 75)
    print("MRPL SOVEREIGN WORKBENCH · HARDWARE-ADAPTIVE MODEL REGISTRY")
    print("=" * 75)
    print(f"Active Profile  : {result['active_profile']}")
    print(f"System RAM      : {result['hardware_detected']['system_ram_gb']} GB (Real: {result['hardware_detected']['real_ram_gb']} GB)")
    print(f"GPU VRAM        : {result['hardware_detected']['gpu_vram_gb']} GB (Device: {result['hardware_detected']['gpu_device']})")
    print(f"CPU Topology    : {result['hardware_detected']['cpu_cores']} logical / {result['hardware_detected']['cpu_physical_cores']} physical cores")
    print(f"Selection Reason: {result['reasoning']}")
    print("\nAssigned Role-Model Mapping:")
    for role, m in result["models"].items():
        print(f"  • {role:28s} -> {m.get('ollama_tag'):22s} [{m.get('license')}] | {m.get('role')}")
    print("=" * 75)
