#!/usr/bin/env python3
"""
================================================================================
SIH 2026: STRICT EGRESS DENYLIST & AIR-GAP COMPLIANCE GUARD (TASK L20)
Project PS-26117 · Sovereign On-Premise Agentic AI Workbench (MRPL)
Intercepts all outbound socket, urllib, requests, and httpx requests.
Blocks cloud APIs (*.aliyuncs.com, api.mistral.ai, api.deepseek.com, etc.)
and enforces 100% loopback isolation (127.0.0.1 / localhost).
================================================================================
"""

import os
import sys
import socket
import urllib.request
import urllib.error
import fnmatch
from pathlib import Path
from typing import Optional, List, Tuple
from urllib.parse import urlparse

base_dir = Path(__file__).resolve().parent.parent
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

from security.ledger import audit_ledger

class SecurityEgressViolationError(PermissionError):
    """Raised when any code path attempts outbound egress to a forbidden cloud host."""
    pass

# Explicit Denylist of Cloud Sibling APIs & Non-Local Hostnames
FORBIDDEN_CLOUD_PATTERNS = [
    "*.aliyuncs.com",
    "dashscope.*.com",
    "*.dashscope.aliyuncs.com",
    "api.mistral.ai",
    "*.mistral.ai",
    "api.deepseek.com",
    "*.deepseek.com",
    "generativelanguage.googleapis.com",
    "*.googleapis.com",
    "api.openai.com",
    "*.openai.com",
    "api.anthropic.com",
    "*.anthropic.com",
    "api.groq.com",
    "api.cohere.ai",
    "api.together.xyz",
    "*.huggingface.co"
]

ALLOWED_HOSTS = {
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "::1"
}

class AirgapComplianceGuard:
    _installed = False

    @staticmethod
    def is_host_allowed(host: str) -> bool:
        if not host:
            return False
        clean_host = host.split(":")[0].strip().lower()
        if clean_host in ALLOWED_HOSTS:
            return True
        return False

    @staticmethod
    def check_destination(url_or_host: str) -> None:
        """
        Validates the host before connection. Raises SecurityEgressViolationError if forbidden.
        """
        host = url_or_host
        if "://" in url_or_host:
            parsed = urlparse(url_or_host)
            host = parsed.hostname or url_or_host

        clean_host = host.split(":")[0].strip().lower()

        # Check explicit denylist patterns
        for pattern in FORBIDDEN_CLOUD_PATTERNS:
            if fnmatch.fnmatch(clean_host, pattern.lower()):
                AirgapComplianceGuard._log_and_raise(clean_host, f"Matched explicit cloud denylist pattern '{pattern}'")

        # Strict allowlist check: anything other than 127.0.0.1 / localhost is rejected
        if clean_host not in ALLOWED_HOSTS:
            AirgapComplianceGuard._log_and_raise(clean_host, "Destination host is not localhost/127.0.0.1 (Zero Egress Violation)")

    @staticmethod
    def _log_and_raise(target_host: str, reason: str):
        msg = (
            f"[CRITICAL SECURITY GUARD] Outbound cloud egress BLOCKED to host '{target_host}'. "
            f"Reason: {reason}. SIH 2026 Invariant I1 (Zero Egress) Enforced."
        )
        # Log CRITICAL security breach attempt to Ed25519 tamper-evident ledger
        try:
            audit_ledger.append_entry(
                event_type="SECURITY_EGRESS_VIOLATION_BLOCKED",
                component="AirgapComplianceGuard",
                payload={
                    "target_host": target_host,
                    "reason": reason,
                    "action": "BLOCKED_RAISE_EXCEPTION",
                    "severity": "CRITICAL"
                },
                severity="CRITICAL"
            )
        except Exception:
            pass

        raise SecurityEgressViolationError(msg)

    @classmethod
    def install(cls):
        """
        Installs low-level socket and urllib interception hooks.
        """
        if cls._installed:
            return
        
        # 1. Hook socket.create_connection
        orig_create_connection = socket.create_connection

        def guarded_create_connection(address, *args, **kwargs):
            host = address[0] if isinstance(address, tuple) else address
            cls.check_destination(str(host))
            return orig_create_connection(address, *args, **kwargs)

        socket.create_connection = guarded_create_connection

        # 2. Hook socket.socket.connect
        orig_connect = socket.socket.connect

        def guarded_connect(sock_self, address):
            host = address[0] if isinstance(address, tuple) else address
            cls.check_destination(str(host))
            return orig_connect(sock_self, address)

        socket.socket.connect = guarded_connect

        # 3. Hook urllib.request.urlopen
        orig_urlopen = urllib.request.urlopen

        def guarded_urlopen(url, *args, **kwargs):
            if isinstance(url, urllib.request.Request):
                target_url = url.full_url
            else:
                target_url = str(url)
            cls.check_destination(target_url)
            return orig_urlopen(url, *args, **kwargs)

        urllib.request.urlopen = guarded_urlopen

        # 4. Hook requests if present
        try:
            import requests
            orig_send = requests.Session.send

            def guarded_send(self_session, request, **kwargs):
                cls.check_destination(request.url)
                return orig_send(self_session, request, **kwargs)

            requests.Session.send = guarded_send
        except ImportError:
            pass

        cls._installed = True

# Install guard upon module load
compliance_guard = AirgapComplianceGuard()
compliance_guard.install()

if __name__ == "__main__":
    print("Airgap Compliance Guard Initialized & Active.")
    print("Testing localhost permission:")
    try:
        AirgapComplianceGuard.check_destination("http://127.0.0.1:11434/api/tags")
        print("  ✓ Localhost 127.0.0.1 permitted successfully.")
    except Exception as e:
        print("  ✗ Error on localhost:", e)

    print("\nTesting deliberate blocked call to api.deepseek.com:")
    try:
        AirgapComplianceGuard.check_destination("https://api.deepseek.com/v1/chat/completions")
        print("  ✗ FAILURE: Cloud call was NOT blocked!")
    except SecurityEgressViolationError as sve:
        print("  ✓ SUCCESS: Cloud call was BLOCKED with SecurityEgressViolationError:")
        print(f"    --> {sve}")
