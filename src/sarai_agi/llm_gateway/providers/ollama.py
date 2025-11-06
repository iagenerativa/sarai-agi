"""Simple Ollama provider adapter.

This is a lightweight adapter that issues a POST to the configured Ollama
HTTP API. It intentionally keeps payloads simple so it can be adapted to
different Ollama API variants via configuration.
"""
import json
import requests
from typing import List, Dict


class OllamaProvider:
    def __init__(self, base_url: str, model: str, timeout: int = 300):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(self, messages: List[Dict], **kwargs) -> Dict:
        """Send chat/completion request to Ollama.

        Returns a dict with at least `text` key.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "messages": messages,
        }
        # merge kwargs into payload for extensibility
        payload.update(kwargs)

        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        try:
            data = resp.json()
        except ValueError:
            # fallback to raw text
            return {"text": resp.text}

        # Ollama variants may return {"output": "..."} or {"choices": [...]}
        if isinstance(data, dict):
            if "output" in data:
                return {"text": data["output"]}
            if "text" in data:
                return {"text": data["text"]}
            if "choices" in data and data["choices"]:
                c = data["choices"][0]
                return {"text": c.get("text") or c.get("message")}

        # fallback: stringify
        return {"text": json.dumps(data)}

