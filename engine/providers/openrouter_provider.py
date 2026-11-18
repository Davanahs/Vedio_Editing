"""
OpenRouter provider — LLM Director using free models via httpx.
"""
from __future__ import annotations

import json
import os
import re
import ast
import logging
from typing import Optional, Dict, Any
import httpx

from .base import DirectorProvider, DirectorResult

logger = logging.getLogger(__name__)

class OpenRouterDirectorProvider(DirectorProvider):
    """
    Uses OpenRouter API with verified free models:
    1. nvidia/nemotron-3.5-lightning:free
    2. google/gemma-4-31b-it:free
    3. liquid/lfm-3-1.7b:free
    """

    BASE_URL = "https://openrouter.ai/api/v1"
    FREE_MODELS = [
        "nvidia/nemotron-3.5-lightning:free",
        "google/gemma-4-31b-it:free",
        "liquid/lfm-3-1.7b:free",
    ]
    SITE_URL = "https://github.com/reel-editor"
    APP_NAME = "Reel Editor AI Engine"

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. Get a free key at https://openrouter.ai"
            )
        self._used_model = self.FREE_MODELS[0]

    @property
    def name(self) -> str:
        return f"OpenRouter ({self._used_model})"

    def _extract_json(self, text: Optional[str]) -> dict:
        if not text:
            raise ValueError("Empty or None text returned from model")

        # Strip markdown fences
        clean = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            json_str = clean[start : end + 1]
            try:
                return json.loads(json_str)
            except Exception:
                pass

            try:
                val = ast.literal_eval(json_str)
                if isinstance(val, dict):
                    return val
            except Exception:
                pass

            try:
                fixed = re.sub(r",\s*([\]}])", r"\1", json_str)
                fixed = re.sub(r"(?<=[{,\s])'([a-zA-Z0-9_]+)':", r'"\1":', fixed)
                return json.loads(fixed)
            except Exception:
                pass

        raise ValueError(f"No valid JSON object found in response: {text[:120]}")

    async def generate_edl(self, prompt: str, context: dict = None) -> DirectorResult:
        context = context or {}
        full_prompt = prompt
        if context:
            full_prompt = f"{prompt}\n\nContext:\n{json.dumps(context, indent=2)}"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": self.SITE_URL,
            "X-Title": self.APP_NAME,
            "Content-Type": "application/json",
        }

        last_err = None

        for model in self.FREE_MODELS:
            self._used_model = model
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional video director. Return ONLY a single raw valid JSON object. Never output markdown code blocks, thoughts, or explanations. Start with '{' and end with '}'."
                    },
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2048,
            }

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload
                    )

                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise ValueError(f"No choices returned: {data}")

                    msg = choices[0].get("message", {})
                    content = msg.get("content") or ""
                    
                    if not content and "reasoning" in msg:
                        content = msg["reasoning"]

                    edl_dict = self._extract_json(content)
                    tokens = data.get("usage", {}).get("total_tokens", 0)
                    return DirectorResult(
                        edl=edl_dict,
                        model_used=model,
                        tokens_used=tokens
                    )
                else:
                    logger.warning(f"OpenRouter model {model} status {resp.status_code}")
                    last_err = f"Status {resp.status_code}: {resp.text[:100]}"
            except Exception as e:
                logger.warning(f"OpenRouter model {model} error: {e}")
                last_err = str(e)

        raise RuntimeError(f"All OpenRouter models failed. Last error: {last_err}")
