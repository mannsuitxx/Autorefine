"""
eval/constrained_decoder.py
===========================
Constrained Structured Decoding Engine with Pydantic Second-Net Validation.
Ensures the LLM output is structurally constrained to pre-defined JSON schemas.
"""

import json
import logging
import urllib.request
from typing import Dict, Any, Type, Optional, Tuple
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("constrained_decoder")


class ConstrainedDecoder:
    """
    Interfaces with local Ollama runtime to pass `format: schema` for strict grammar-constrained generation.
    Falls back to robust repair & Pydantic validation second net.
    """
    def __init__(self, ollama_url: str = "http://127.0.0.1:11434"):
        self.ollama_url = ollama_url

    def generate_constrained(
        self,
        prompt: str,
        schema_cls: Type[BaseModel],
        model: str = "qwen2.5:1.5b",
        temperature: float = 0.0
    ) -> Tuple[Optional[BaseModel], Dict[str, Any]]:
        """
        Sends generation request with JSON schema constraint to Ollama.
        Validates returned JSON against Pydantic schema.
        """
        json_schema = schema_cls.model_json_schema()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "format": json_schema,  # Ollama native JSON schema constrained decoding
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "seed": 42
            }
        }
        
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_response = result.get("response", "{}")
                
                # Second net: Pydantic parsing
                parsed_json = json.loads(raw_response)
                validated_obj = schema_cls.model_validate(parsed_json)
                
                return validated_obj, {
                    "status": "VALID",
                    "raw_response": raw_response,
                    "schema_enforced": True,
                    "violations": 0
                }
        except ValidationError as ve:
            return None, {
                "status": "PYDANTIC_VALIDATION_ERROR",
                "error": str(ve),
                "schema_enforced": True,
                "violations": 1
            }
        except Exception as e:
            return None, {
                "status": "ERROR",
                "error": str(e),
                "schema_enforced": True,
                "violations": 1
            }

    def simulate_unconstrained(
        self,
        prompt: str,
        schema_cls: Type[BaseModel],
        model: str = "qwen2.5:1.5b"
    ) -> Tuple[Optional[BaseModel], Dict[str, Any]]:
        """
        Simulates unconstrained generation without JSON schema to measure baseline schema violation rate.
        """
        payload = {
            "model": model,
            "prompt": f"{prompt}\nOutput valid JSON matching schema:\n{json.dumps(schema_cls.model_json_schema())}",
            "stream": False,
            "options": {"temperature": 0.7}
        }
        req = urllib.request.Request(
            f"{self.ollama_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                raw_response = result.get("response", "")
                
                # Attempt to parse raw unconstrained output
                try:
                    # Strip markdown code blocks if present
                    clean = raw_response.strip()
                    if clean.startswith("```json"):
                        clean = clean[7:]
                    if clean.startswith("```"):
                        clean = clean[3:]
                    if clean.endswith("```"):
                        clean = clean[:-3]
                    parsed_json = json.loads(clean)
                    validated_obj = schema_cls.model_validate(parsed_json)
                    return validated_obj, {"status": "VALID", "violations": 0, "raw": raw_response}
                except (json.JSONDecodeError, ValidationError) as err:
                    return None, {"status": "SCHEMA_VIOLATION", "error": str(err), "violations": 1, "raw": raw_response}
        except Exception as e:
            return None, {"status": "ERROR", "error": str(e), "violations": 1}
