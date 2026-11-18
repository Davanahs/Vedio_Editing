"""
Gemini provider — LLM Director using google-generativeai.
"""
from __future__ import annotations

import json
import os
import re

from .base import DirectorProvider, DirectorResult

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmBlockThreshold, HarmCategory
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False


class GeminiDirectorProvider(DirectorProvider):
    """
    Uses Gemini 2.0 Flash Lite (or 1.5 Flash fallback) to generate EDL JSON.
    """

    PRIMARY_MODEL = "gemini-2.0-flash-lite"
    FALLBACK_MODEL = "gemini-1.5-flash"

    def __init__(self, api_key: str | None = None):
        if not _GENAI_AVAILABLE:
            raise ImportError(
                "google-generativeai not installed. Run: pip install google-generativeai>=0.8.0"
            )
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Get your key at https://aistudio.google.com"
            )
        genai.configure(api_key=self._api_key)
        self._model_name = self.PRIMARY_MODEL
        self._client = self._make_client(self.PRIMARY_MODEL)

    def _make_client(self, model_name: str):
        safety = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        }
        return genai.GenerativeModel(
            model_name=model_name,
            safety_settings=safety,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                max_output_tokens=4096,
            ),
        )

    @property
    def name(self) -> str:
        return f"Gemini ({self._model_name})"

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from markdown-wrapped or bare response."""
        # Try stripping markdown code fences
        clean = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        # Find the outermost { ... }
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            json_str = clean[start : end + 1]
            return json.loads(json_str)
        raise ValueError("No JSON object found in response")

    async def generate_edl(self, prompt: str, context: dict) -> DirectorResult:
        full_prompt = f"{prompt}\n\nContext:\n{json.dumps(context, indent=2)}"

        for model_name in [self.PRIMARY_MODEL, self.FALLBACK_MODEL]:
            if model_name != self._model_name:
                self._client = self._make_client(model_name)
                self._model_name = model_name
            try:
                response = await self._client.generate_content_async(full_prompt)
                raw_text = response.text
                edl = self._extract_json(raw_text)
                tokens = getattr(response, "usage_metadata", None)
                token_count = 0
                if tokens:
                    token_count = getattr(tokens, "total_token_count", 0)
                return DirectorResult(
                    edl=edl,
                    model_used=model_name,
                    tokens_used=token_count,
                    raw_response=raw_text,
                )
            except Exception as e:
                if model_name == self.FALLBACK_MODEL:
                    raise RuntimeError(f"Gemini generation failed: {e}") from e
                # Try fallback model
                continue

        raise RuntimeError("All Gemini models failed")
