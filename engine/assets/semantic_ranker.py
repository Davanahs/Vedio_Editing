"""Offline semantic ranking for catalog assets with a deterministic local fallback."""
from __future__ import annotations

import os
import re
import sys
import threading
from pathlib import Path
from typing import Any

import numpy as np

_MODEL = None
_TOKENIZER = None
_MODEL_PATH: Path | None = None
_MODEL_LOCK = threading.Lock()
_EMBEDDING_CACHE: dict[str, np.ndarray] = {}


def _find_local_model() -> Path | None:
    override = os.getenv("AURA_ASSET_EMBEDDING_MODEL")
    if override and Path(override).is_dir():
        return Path(override)
    cache_root = Path(os.getenv("HF_HUB_CACHE", str(Path.home() / ".cache" / "huggingface" / "hub")))
    snapshots = cache_root / "models--sentence-transformers--all-MiniLM-L6-v2" / "snapshots"
    if not snapshots.is_dir():
        return None
    available = [path for path in snapshots.iterdir() if (path / "modules.json").is_file()]
    return max(available, key=lambda path: path.stat().st_mtime) if available else None


def _get_model():
    global _MODEL, _TOKENIZER, _MODEL_PATH
    if _MODEL is not None:
        return _MODEL
    with _MODEL_LOCK:
        if _MODEL is not None:
            return _MODEL
        model_path = _find_local_model()
        if model_path is None:
            return None
        # Prevent huggingface libraries from attempting any network access.
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        try:
            # Use Transformers directly with attention-mask mean pooling. The
            # sentence-transformers wrapper imports sklearn/pandas, which can
            # crash native extensions in otherwise valid desktop installs.
            # The transformer model needs only torch/tokenizers. Marking the
            # optional sklearn integration unavailable during Transformers'
            # lazy import avoids importing a broken native pyarrow build via
            # pandas/sklearn on some Windows Python installations.
            sentinel = object()
            previous_sklearn = sys.modules.get("sklearn", sentinel)
            sys.modules["sklearn"] = None
            try:
                from transformers import AutoModel, AutoTokenizer
            finally:
                if previous_sklearn is sentinel:
                    sys.modules.pop("sklearn", None)
                else:
                    sys.modules["sklearn"] = previous_sklearn

            _TOKENIZER = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
            _MODEL = AutoModel.from_pretrained(str(model_path), local_files_only=True)
            _MODEL.eval()
            _MODEL_PATH = model_path
        except Exception:
            _MODEL = None
        return _MODEL


def _asset_text(metadata: dict[str, Any]) -> str:
    fields = [
        metadata.get("id", "").replace("_", " "),
        metadata.get("category", "").replace("_", " "),
        metadata.get("visual_description", ""),
        metadata.get("intended_purpose", ""),
        " ".join(metadata.get("keywords", [])),
        " ".join(metadata.get("suitable_content_types", [])),
    ]
    return " ".join(str(value) for value in fields if value).strip()


def _lexical_scores(query: str, documents: list[str]) -> list[float]:
    stop = {"this", "that", "with", "from", "your", "into", "about", "video", "scene", "show", "make", "using", "user", "resource"}
    query_tokens = {token for token in re.findall(r"[a-z0-9]{3,}", query.lower()) if token not in stop}
    results = []
    for document in documents:
        doc_tokens = {token for token in re.findall(r"[a-z0-9]{3,}", document.lower()) if token not in stop}
        if not query_tokens or not doc_tokens:
            results.append(0.0)
            continue
        overlap = len(query_tokens & doc_tokens)
        results.append(overlap / ((len(query_tokens) * len(doc_tokens)) ** 0.5))
    return results


def score_asset_descriptions(query: str, metadata_items: list[dict[str, Any]]) -> tuple[list[float], str]:
    """Return cosine similarity scores and their provenance; no network calls."""
    documents = [_asset_text(item) for item in metadata_items]
    model = _get_model()
    if model is None:
        return _lexical_scores(query, documents), "local_keyword_fallback"
    try:
        import torch

        def encode(texts: list[str]) -> np.ndarray:
            batch = _TOKENIZER(texts, padding=True, truncation=True, max_length=256, return_tensors="pt")
            with torch.inference_mode():
                hidden = model(**batch).last_hidden_state
                mask = batch["attention_mask"].unsqueeze(-1).to(hidden.dtype)
                pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
                return torch.nn.functional.normalize(pooled, p=2, dim=1).cpu().numpy()

        query_vector = encode([query])[0]
        vectors = []
        pending_texts = []
        pending_indices = []
        keys = [f"{_MODEL_PATH}:{document}" for document in documents]
        for index, key in enumerate(keys):
            cached = _EMBEDDING_CACHE.get(key)
            if cached is not None:
                vectors.append((index, cached))
            else:
                pending_texts.append(documents[index])
                pending_indices.append((index, key))
        if pending_texts:
            encoded = encode(pending_texts)
            for (index, key), vector in zip(pending_indices, encoded):
                _EMBEDDING_CACHE[key] = np.asarray(vector, dtype=np.float32)
                vectors.append((index, _EMBEDDING_CACHE[key]))
        vectors.sort(key=lambda item: item[0])
        return [float(np.dot(query_vector, vector)) for _, vector in vectors], "sentence-transformers/all-MiniLM-L6-v2"
    except Exception:
        return _lexical_scores(query, documents), "local_keyword_fallback"
