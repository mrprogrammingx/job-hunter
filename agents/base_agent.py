import os
import json
from anthropic import Anthropic
from core.band import Band


class BaseAgent:
    model = "claude-sonnet-4-6"

    def __init__(self, band: Band, name: str):
        self.band = band
        self.name = name
        self._client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def _llm(self, system: str, user: str, max_tokens: int = 4096) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text

    def _llm_json(self, system: str, user: str, max_tokens: int = 4096) -> dict:
        raw = self._llm(system, user + "\n\nRespond with valid JSON only, no markdown.", max_tokens)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
