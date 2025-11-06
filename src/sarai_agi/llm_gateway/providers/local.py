"""A trivial local provider for development and testing.

It echos the user's message or performs a simple deterministic transformation.
"""
from typing import List, Dict


class LocalProvider:
    def __init__(self, base_url: str = None, model: str = "local", timeout: int = 30):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def chat(self, messages: List[Dict], **kwargs) -> Dict:
        # Join all user messages to a single reply for simplicity
        parts = []
        for m in messages:
            role = m.get("role")
            content = m.get("content")
            if role == "user":
                parts.append(content)
        joined = " ".join(parts) if parts else ""
        reply = f"[local:{self.model}] {joined[::-1]}"  # return reversed text as deterministic output
        return {"text": reply}

