"""Benchmark contamination defense for fin-reasoning-eval.

Detects potential data contamination where an evaluated model may have been
trained on benchmark problems. Non-blocking: logs warnings, does not fail
evaluation.

Two detection strategies:
  Strategy A — Exact verbatim matching (stdlib only, always active):
    Slide a window across the problem text; flag if any substring longer
    than VERBATIM_THRESHOLD_CHARS appears verbatim in the model response.
  Strategy B — Semantic similarity (optional, requires sentence-transformers):
    Flag when cosine similarity between problem and response embeddings
    exceeds SEMANTIC_SIMILARITY_THRESHOLD.

# module_version: 1.0.0
# date: 2026-04-04
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Verbatim detection threshold in characters.
VERBATIM_THRESHOLD_CHARS: int = 50

# Semantic similarity threshold (cosine).  Requires sentence-transformers.
SEMANTIC_SIMILARITY_THRESHOLD: float = 0.95

# Default path for the persisted hash index.
_DEFAULT_HASHES_PATH = Path(__file__).parent.parent / "data" / "problem_hashes.json"


@dataclass
class ContaminationResult:
    """Result of a contamination check for a single problem/response pair."""

    problem_id: str
    is_flagged: bool
    detection_method: str  # "verbatim" | "semantic" | "none"
    similarity_score: float = 0.0
    matched_fragment: str = ""  # verbatim fragment found, if any
    warning_message: str = ""


class ContaminationChecker:
    """Checks model responses for potential benchmark contamination.

    Non-blocking: all detection methods return results and log warnings.
    Never raises on detection; only raises on configuration/IO errors.

    Args:
        hashes_path: Path to the JSON file used to persist the hash index.
            Defaults to data/problem_hashes.json in the repo root.
        use_semantic: Opt-in flag.  When True, attempts to load
            sentence-transformers and enables cosine-similarity checks.
            Silently degrades to verbatim-only if the library is absent.
    """

    def __init__(
        self,
        hashes_path: Optional[Path | str] = None,
        use_semantic: bool = False,
    ) -> None:
        self._hashes_path: Path = (
            Path(hashes_path) if hashes_path is not None else _DEFAULT_HASHES_PATH
        )
        self._use_semantic: bool = use_semantic
        self._hash_index: dict[str, str] = {}

        # Attempt to load sentence-transformers if semantic mode requested.
        self._embedder = None
        if use_semantic:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore

                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("ContaminationChecker: sentence-transformers loaded.")
            except ImportError:
                logger.warning(
                    "ContaminationChecker: sentence-transformers not installed; "
                    "semantic similarity checks disabled."
                )

    # ------------------------------------------------------------------
    # Hash index helpers
    # ------------------------------------------------------------------

    def build_hash_index(self, problems: list) -> dict[str, str]:
        """Build SHA-256 hash index from a list of problem objects.

        Accepts either FinancialReasoningExample instances (with .id,
        .question, .context attributes) or plain dicts with equivalent keys.

        Args:
            problems: Iterable of problem objects or dicts.

        Returns:
            Mapping of {problem_id: sha256_hex}.
        """
        index: dict[str, str] = {}
        for p in problems:
            if hasattr(p, "id"):
                pid = p.id
                text = _extract_problem_text(p.question, p.context)
            else:
                pid = p.get("id", "")
                text = _extract_problem_text(
                    p.get("question", ""), p.get("context", "")
                )
            index[pid] = self._compute_hash(text)
        self._hash_index = index
        return index

    def save_hash_index(self, index: dict[str, str], path: Path) -> None:
        """Persist hash index to JSON.

        Args:
            index: Mapping of {problem_id: sha256_hex}.
            path: Destination file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(index, fh, indent=2, sort_keys=True)
        logger.info("ContaminationChecker: hash index saved to %s (%d entries).", path, len(index))

    def load_hash_index(self, path: Path) -> dict[str, str]:
        """Load hash index from JSON.

        Args:
            path: Source file path.

        Returns:
            Mapping of {problem_id: sha256_hex}, or empty dict if file absent.
        """
        path = Path(path)
        if not path.exists():
            logger.warning("ContaminationChecker: hash index not found at %s.", path)
            return {}
        with open(path, "r", encoding="utf-8") as fh:
            index: dict[str, str] = json.load(fh)
        self._hash_index = index
        logger.info("ContaminationChecker: loaded hash index from %s (%d entries).", path, len(index))
        return index

    # ------------------------------------------------------------------
    # Single-response check
    # ------------------------------------------------------------------

    def check_response(
        self,
        problem_id: str,
        problem_text: str,
        model_response: str,
        response_embedding: Optional[List[float]] = None,
        problem_embedding: Optional[List[float]] = None,
    ) -> ContaminationResult:
        """Check a single model response for contamination signals.

        Runs verbatim detection first.  If use_semantic=True and embeddings
        are provided (or can be computed), also runs semantic similarity.

        Args:
            problem_id: Identifier for the problem (for reporting).
            problem_text: The original problem text (question + context).
            model_response: The model's full response string.
            response_embedding: Pre-computed response embedding (optional).
            problem_embedding: Pre-computed problem embedding (optional).

        Returns:
            ContaminationResult with is_flagged=True if any signal fires.
        """
        # Strategy A: verbatim
        verbatim_flagged, fragment = self._check_verbatim(problem_text, model_response)
        if verbatim_flagged:
            msg = (
                f"CONTAMINATION WARNING [{problem_id}]: verbatim fragment "
                f"({len(fragment)} chars) found in model response."
            )
            logger.warning(msg)
            return ContaminationResult(
                problem_id=problem_id,
                is_flagged=True,
                detection_method="verbatim",
                similarity_score=1.0,
                matched_fragment=fragment,
                warning_message=msg,
            )

        # Strategy B: semantic (opt-in)
        if self._use_semantic:
            p_emb = problem_embedding
            r_emb = response_embedding

            # Compute on-the-fly if embedder is available and embeddings absent.
            if self._embedder is not None:
                if p_emb is None:
                    p_emb = self._embedder.encode(problem_text).tolist()
                if r_emb is None:
                    r_emb = self._embedder.encode(model_response).tolist()

            if p_emb is not None and r_emb is not None:
                sim = self._check_semantic(p_emb, r_emb)
                if sim >= SEMANTIC_SIMILARITY_THRESHOLD:
                    msg = (
                        f"CONTAMINATION WARNING [{problem_id}]: semantic similarity "
                        f"{sim:.4f} >= threshold {SEMANTIC_SIMILARITY_THRESHOLD}."
                    )
                    logger.warning(msg)
                    return ContaminationResult(
                        problem_id=problem_id,
                        is_flagged=True,
                        detection_method="semantic",
                        similarity_score=sim,
                        warning_message=msg,
                    )

        return ContaminationResult(
            problem_id=problem_id,
            is_flagged=False,
            detection_method="none",
        )

    # ------------------------------------------------------------------
    # Batch check
    # ------------------------------------------------------------------

    def check_batch(
        self,
        problems_and_responses: List[Tuple[str, str, str]],
    ) -> List[ContaminationResult]:
        """Check a batch of responses.

        Args:
            problems_and_responses: List of (problem_id, problem_text, response).

        Returns:
            List of ContaminationResult, one per input tuple.
        """
        results: List[ContaminationResult] = []
        for problem_id, problem_text, response in problems_and_responses:
            result = self.check_response(
                problem_id=problem_id,
                problem_text=problem_text,
                model_response=response,
            )
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    def generate_report(self, results: List[ContaminationResult]) -> dict:
        """Summarize contamination check results across a full eval run.

        Args:
            results: List of ContaminationResult objects.

        Returns:
            Summary dict with totals, rates, and per-method breakdowns.
        """
        flagged = [r for r in results if r.is_flagged]
        total = len(results)
        return {
            "total_checked": total,
            "flagged_count": len(flagged),
            "flagged_rate": len(flagged) / max(total, 1),
            "flagged_problem_ids": [r.problem_id for r in flagged],
            "detection_methods": {
                m: sum(1 for r in flagged if r.detection_method == m)
                for m in ("verbatim", "semantic")
            },
        }

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_hash(problem_text: str) -> str:
        """Return SHA-256 hex digest of problem_text (UTF-8 encoded)."""
        return hashlib.sha256(problem_text.encode("utf-8")).hexdigest()

    def _check_verbatim(
        self, problem_text: str, model_response: str
    ) -> Tuple[bool, str]:
        """Slide a window across problem_text; return (flagged, fragment).

        Checks every substring of length VERBATIM_THRESHOLD_CHARS from
        problem_text against model_response.  Returns on first match.
        Case-sensitive to avoid false positives from common short phrases.

        Args:
            problem_text: Source problem text.
            model_response: Model's response string.

        Returns:
            Tuple of (is_flagged, matched_fragment).
        """
        threshold = VERBATIM_THRESHOLD_CHARS
        if len(problem_text) < threshold:
            return False, ""

        # Use a step of 1 for thorough coverage; bail out on first hit.
        for start in range(0, len(problem_text) - threshold + 1):
            fragment = problem_text[start : start + threshold]
            if fragment in model_response:
                return True, fragment

        return False, ""

    def _check_semantic(
        self,
        problem_embedding: List[float],
        response_embedding: List[float],
    ) -> float:
        """Compute cosine similarity between two embedding vectors.

        Uses pure-Python math; does not require numpy.

        Args:
            problem_embedding: Embedding for the problem text.
            response_embedding: Embedding for the model response.

        Returns:
            Cosine similarity in [0, 1].
        """
        dot = sum(a * b for a, b in zip(problem_embedding, response_embedding))
        norm_p = math.sqrt(sum(a * a for a in problem_embedding))
        norm_r = math.sqrt(sum(b * b for b in response_embedding))
        if norm_p == 0.0 or norm_r == 0.0:
            return 0.0
        return dot / (norm_p * norm_r)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _extract_problem_text(question: str, context: object) -> str:
    """Combine question and context into a single string for hashing.

    Context may be a string (already formatted) or a dict (raw JSON form).
    """
    if isinstance(context, dict):
        ctx_str = json.dumps(context, sort_keys=True)
    else:
        ctx_str = str(context) if context else ""
    return f"{question}\n{ctx_str}"
