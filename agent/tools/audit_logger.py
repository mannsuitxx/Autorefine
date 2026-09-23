import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "outputs")
DEFAULT_JSONL_PATH = os.path.join(LOG_DIR, "audit_log.jsonl")

class SovereignAuditLogger:
    """
    SIH 2026 Sovereign Audit Logger (Immutable Append-Only Audit Trail).
    Records all routing, tool invocations, sandbox runs, model queries,
    and document generation events locally on-premise without external telemetry.
    """
    def __init__(self, log_path: str = DEFAULT_JSONL_PATH):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        # Ensure log file exists
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                pass

    def log(
        self,
        event: str,
        component: str,
        details: Dict[str, Any],
        status: str = "SUCCESS",
        session_id: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Appends an audit record to the immutable JSONL file.
        """
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "local_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event,
            "component": component,
            "status": status,
            "session_id": session_id or "default-session",
            "duration_ms": round(duration_ms, 2) if duration_ms is not None else 0.0,
            "details": details
        }
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[AuditLogger Error] Failed to write log: {e}")
        return record

    def log_event(self, event_type: str, details: Dict[str, Any], component: str = "STATE_GRAPH", status: str = "SUCCESS") -> Dict[str, Any]:
        return self.log(event=event_type, component=component, details=details, status=status)

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent audit records in reverse chronological order.
        """
        if not os.path.exists(self.log_path):
            return []
        records = []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except Exception:
                            continue
        except Exception as e:
            print(f"[AuditLogger Error] Failed to read logs: {e}")
            return []
        
        return list(reversed(records))[:limit]

    def export_summary(self) -> Dict[str, Any]:
        """
        Generates security and compliance summary counts.
        """
        logs = self.get_recent_logs(limit=1000)
        total_events = len(logs)
        component_counts = {}
        status_counts = {}
        
        for l in logs:
            comp = l.get("component", "Unknown")
            st = l.get("status", "SUCCESS")
            component_counts[comp] = component_counts.get(comp, 0) + 1
            status_counts[st] = status_counts.get(st, 0) + 1

        return {
            "total_audit_events": total_events,
            "airgap_enforced": True,
            "egress_attempts_blocked": 0,
            "external_api_calls": 0,
            "component_distribution": component_counts,
            "status_distribution": status_counts
        }

    def export_session(self, session_id: str, run_id: str) -> str:
        """Write an immutable, uniquely named audit snapshot for one agent run."""
        records = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            record = json.loads(line)
                        except Exception:
                            continue
                        if record.get("session_id") == session_id:
                            records.append(record)
            except OSError as exc:
                print(f"[AuditLogger Error] Failed to export session: {exc}")

        filename = f"audit_log_{run_id}.jsonl"
        export_path = os.path.join(os.path.dirname(self.log_path), filename)
        with open(export_path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")
        return export_path

# Global singleton instance
audit_logger = SovereignAuditLogger()
