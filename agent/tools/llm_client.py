import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

class LocalLLMClient:
    """
    Direct HTTP client for local Ollama open-weight model serving.
    Fails loudly if the model is unreachable or returns an error.
    """
    def __init__(self, host: str = "http://127.0.0.1:11434"):
        self.host = host.rstrip("/")
        self.chat_endpoint = f"{self.host}/api/chat"
        self.tags_endpoint = f"{self.host}/api/tags"

    def installed_models(self, timeout_sec: int = 3) -> List[str]:
        """Return model names actually installed in the local Ollama runtime."""
        req = urllib.request.Request(self.tags_endpoint, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                if response.status != 200:
                    return []
                payload = json.loads(response.read().decode("utf-8"))
                return [item.get("name", "") for item in payload.get("models", []) if item.get("name")]
        except (urllib.error.URLError, TimeoutError, ValueError):
            return []

    def resolve_model(self, preferred: str, fallback: Optional[str] = None) -> str:
        """Resolve a configured role to an installed local model, never a fabricated tag."""
        installed = self.installed_models()
        if not installed:
            raise RuntimeError(
                "No local Ollama models are available at "
                f"{self.host}. Install at least one configured model before running a task."
            )
        for candidate in (preferred, fallback):
            if candidate and any(name == candidate or name.startswith(candidate + ":") for name in installed):
                return next(name for name in installed if name == candidate or name.startswith(candidate + ":"))
        raise RuntimeError(
            f"Neither configured model '{preferred}' nor fallback '{fallback}' is installed. "
            f"Installed local models: {', '.join(installed)}"
        )

    def chat(self, model: str, messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 150, timeout_sec: int = 90) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.chat_endpoint,
            data=data_bytes,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                if response.status != 200:
                    raise RuntimeError(f"Ollama server returned HTTP status {response.status}")
                raw = response.read().decode("utf-8")
                res = json.loads(raw)
                content = res.get("message", {}).get("content", "")
                
                return {
                    "content": content,
                    "model": res.get("model", model),
                    "eval_count": res.get("eval_count", 0),
                    "total_duration_sec": round(res.get("total_duration", 0) / 1e9, 3),
                    "raw_response": res
                }
        except urllib.error.URLError as e:
            raise RuntimeError(f"Failed to connect to local Ollama runtime at {self.chat_endpoint}: {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Ollama inference error on model '{model}': {e}")
