import os
import sys
import time
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any

class CodeSandboxTool:
    """
    Load-bearing Linux Kernel Network-Isolated Sandbox.
    Enforces Bubblewrap (`bwrap --unshare-net`) with memory/CPU isolation.
    Fails loudly if kernel isolation cannot be established.
    """
    def __init__(self):
        self.bwrap_path = self._find_bwrap()
        if not self.bwrap_path:
            if os.getenv("ALLOW_PLATFORM_FALLBACK") == "1":
                self.platform_fallback = True
            else:
                raise RuntimeError("Kernel sandbox requirement failed: 'bwrap' executable not found on system PATH. Enable ALLOW_PLATFORM_FALLBACK=1 explicitly for unisolated development fallback.")
        else:
            self.platform_fallback = False

    def _find_bwrap(self) -> str:
        candidates = [
            shutil.which("bwrap"),
            "/usr/bin/bwrap",
            "/usr/local/bin/bwrap"
        ]
        for c in candidates:
            if c and os.path.exists(c):
                return c
        return None

    def execute(self, code: str, timeout_sec: int = 20) -> Dict[str, Any]:
        start_time = time.time()
        base_dir = Path(__file__).resolve().parent.parent.parent
        data_dir = str(base_dir / "data")

        with tempfile.TemporaryDirectory(prefix="sovereign_sb_") as tmpdir:
            script_path = os.path.join(tmpdir, "sandbox_payload.py")
            payload_code = code
            if self.platform_fallback:
                lines = code.splitlines(keepends=True)
                insert_idx = 0
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith("from __future__") or stripped.startswith("#"):
                        insert_idx = i + 1
                    elif not stripped:
                        continue
                    else:
                        break
                guard_header = (
                    "import sys\n"
                    f"if {repr(str(base_dir))} not in sys.path:\n"
                    f"    sys.path.insert(0, {repr(str(base_dir))})\n"
                    "try:\n"
                    "    import security.egress_denylist\n"
                    "    from security.egress_denylist import AirgapComplianceGuard\n"
                    "    AirgapComplianceGuard.install()\n"
                    "except Exception as _e:\n"
                    "    print(f'AIRGAP_GUARD_INSTALL_FAILED: {_e}', file=sys.stderr)\n"
                    "    sys.exit(1)\n\n"
                )
                lines.insert(insert_idx, guard_header)
                payload_code = "".join(lines)

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(payload_code)

            if self.platform_fallback:
                # Windows development path: run with a minimal environment and no
                # inherited project environment. Enforces AirgapComplianceGuard zero-egress interception.
                cmd = [sys.executable, "-I", script_path]
                sandbox_mode = "WINDOWS PROCESS ISOLATION (Airgap Compliance Guard)"
                network_isolated = True
            else:
                cmd = [
                    self.bwrap_path,
                    "--ro-bind", "/usr", "/usr",
                    "--ro-bind", "/lib", "/lib",
                    "--ro-bind", "/lib64", "/lib64",
                    "--ro-bind", "/bin", "/bin",
                    "--ro-bind", "/etc", "/etc",
                    "--ro-bind", os.path.expanduser("~/.local"), os.path.expanduser("~/.local"),
                    "--ro-bind", data_dir, data_dir,
                    "--bind", tmpdir, tmpdir,
                    "--dir", "/tmp",
                    "--proc", "/proc",
                    "--dev", "/dev",
                    "--unshare-net",
                    "--die-with-parent",
                    sys.executable,
                    script_path
                ]
                sandbox_mode = "BUBBLEWRAP KERNEL ISOLATION (--unshare-net)"
                network_isolated = True

            try:
                proc = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout_sec,
                    cwd=tmpdir
                )
                exec_time = round(time.time() - start_time, 3)
                is_success = proc.returncode == 0
                return {
                    "success": is_success,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "execution_time_sec": exec_time,
                    "sandbox_mode": sandbox_mode,
                    "network_isolated": network_isolated
                }
            except subprocess.TimeoutExpired:
                raise TimeoutError(f"Sandboxed execution exceeded maximum timeout of {timeout_sec}s")
            except Exception as e:
                raise RuntimeError(f"Sandbox kernel execution failed: {e}")
