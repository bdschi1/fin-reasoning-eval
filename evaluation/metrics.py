"""
Evaluation Metrics for Financial Reasoning Eval Benchmark

Implements metrics for assessing LLM performance on financial reasoning tasks:
- Accuracy (overall, by category, by difficulty)
- Reasoning quality assessment
- Calibration metrics
"""

import re
from typing import Optional, Union
from dataclasses import dataclass, field
from collections import defaultdict

from .calibration import (
    brier_score,
    expected_calibration_error,
    generate_calibration_report,
    log_loss_score,
)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class PredictionResult:
    """Result of a single prediction."""
    problem_id: str
    predicted_answer: str
    correct_answer: str
    is_correct: bool
    category: str
    difficulty: str
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    latency_ms: Optional[float] = None


@dataclass
class EvaluationResults:
    """Aggregated evaluation results."""
    total_examples: int
    overall_accuracy: float
    category_accuracy: dict[str, float]
    difficulty_accuracy: dict[str, float]
    reasoning_quality: Optional[float] = None
    calibration_error: Optional[float] = None
    brier_score_avg: Optional[float] = None
    log_loss_avg: Optional[float] = None
    calibration_per_bin: Optional[list[dict]] = None

    # Detailed breakdown
    correct_count: int = 0
    predictions: list[PredictionResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'total_examples': self.total_examples,
            'overall_accuracy': self.overall_accuracy,
            'category_accuracy': self.category_accuracy,
            'difficulty_accuracy': self.difficulty_accuracy,
            'reasoning_quality': self.reasoning_quality,
            'calibration_error': self.calibration_error,
            'brier_score_avg': self.brier_score_avg,
            'log_loss_avg': self.log_loss_avg,
            'correct_count': self.correct_count,
        }

    def summary(self) -> str:
        """Generate a summary string."""
        lines = [
            f"Total Examples: {self.total_examples}",
            f"Overall Accuracy: {self.overall_accuracy:.1%}",
            "",
            "Accuracy by Category:",
        ]
        for cat, acc in sorted(self.category_accuracy.items()):
            lines.append(f"  {cat}: {acc:.1%}")

        lines.extend(["", "Accuracy by Difficulty:"])
        for diff, acc in sorted(self.difficulty_accuracy.items()):
            lines.append(f"  {diff}: {acc:.1%}")

        if self.reasoning_quality is not None:
            lines.extend(["", f"Reasoning Quality: {self.reasoning_quality:.2f}/5.0"])

        if self.calibration_error is not None:
            lines.extend(["", f"Calibration Error (ECE): {self.calibration_error:.3f}"])

        if self.brier_score_avg is not None:
            lines.append(f"Brier Score (avg): {self.brier_score_avg:.4f}")

        if self.log_loss_avg is not None:
            lines.append(f"Log Loss (avg): {self.log_loss_avg:.4f}")

        return "\n".join(lines)


class FinancialReasoningMetrics:
    """
    Compute evaluation metrics for Financial Reasoning Eval Benchmark.

    Follows HuggingFace evaluate library patterns.
    """

    def __init__(self):
        self._predictions: list[PredictionResult] = []

    def add_prediction(
        self,
        problem_id: str,
        predicted: str,
        reference: str,
        category: str,
        difficulty: str,
        reasoning: Optional[str] = None,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
        answer_type: str = "multiple_choice",
        tolerance: Optional[float] = None,
    ):
        """
        Add a single prediction for evaluation.

        Args:
            problem_id: Unique identifier for the problem
            predicted: Model's predicted answer
            reference: Ground truth answer
            category: Problem category
            difficulty: Problem difficulty
            reasoning: Optional reasoning provided by the model
            confidence: Optional confidence score (0-1)
            latency_ms: Optional inference latency in milliseconds
            answer_type: Type of answer (multiple_choice, numeric, boolean)
            tolerance: Tolerance for numeric answers
        """
        is_correct = self._check_correctness(
            predicted, reference, answer_type, tolerance
        )

        result = PredictionResult(
            problem_id=problem_id,
            predicted_answer=predicted,
            correct_answer=reference,
            is_correct=is_correct,
            category=category,
            difficulty=difficulty,
            reasoning=reasoning,
            confidence=confidence,
            latency_ms=latency_ms,
        )
        self._predictions.append(result)

    def add_batch(
        self,
        predictions: list[dict],
        references: list[dict],
    ):
        """
        Add a batch of predictions.

        Args:
            predictions: List of prediction dicts with 'id', 'predicted', etc.
            references: List of reference dicts with 'id', 'correct_answer', etc.
        """
        ref_map = {r['id']: r for r in references}

        for pred in predictions:
            ref = ref_map.get(pred['id'])
            if ref is None:
                continue

            self.add_prediction(
                problem_id=pred['id'],
                predicted=pred.get('predicted', ''),
                reference=ref.get('correct_answer', ''),
                category=ref.get('category', ''),
                difficulty=ref.get('difficulty', ''),
                reasoning=pred.get('reasoning'),
                confidence=pred.get('confidence'),
                latency_ms=pred.get('latency_ms'),
                answer_type=ref.get('answer_type', 'multiple_choice'),
            )

    def _check_correctness(
        self,
        predicted: str,
        reference: str,
        answer_type: str,
        tolerance: Optional[float] = None,
    ) -> bool:
        """Check if prediction is correct."""
        if answer_type == "numeric":
            return self._check_numeric(predicted, reference, tolerance or 0.01)
        elif answer_type == "boolean":
            return self._check_boolean(predicted, reference)
        else:
            return self._check_text(predicted, reference)

    def _check_numeric(
        self,
        predicted: str,
        reference: str,
        tolerance: float
    ) -> bool:
        """Check numeric answer with tolerance.

        Handles percentage format mismatch: if one value is ~100x the other
        (e.g., model says 14.5% but ground truth is 0.14464), tries both
        scales before failing.
        """
        try:
            pred_val = self._extract_number(predicted)
            ref_val = self._extract_number(reference)

            if pred_val is None or ref_val is None:
                return False

            if ref_val == 0:
                return abs(pred_val) < tolerance

            # Direct comparison
            if abs(pred_val - ref_val) / abs(ref_val) <= tolerance:
                return True

            # Try percentage scaling (pred is 100x ref, e.g., 14.5 vs 0.145)
            if ref_val != 0 and abs(pred_val / 100 - ref_val) / abs(ref_val) <= tolerance:
                return True

            # Try inverse scaling (ref is 100x pred)
            if pred_val != 0 and abs(pred_val - ref_val / 100) / abs(pred_val) <= tolerance:
                return True

            return False
        except (ValueError, ZeroDivisionError):
            return False

    def _extract_number(self, text: str) -> Optional[float]:
        """Extract a number from text, preferring the last number found."""
        # Remove common formatting
        text = text.replace(',', '').replace('$', '').replace('%', '')

        # Find all numbers
        numbers = re.findall(r'-?\d+\.?\d*', text)
        if not numbers:
            return None

        # If only one number, return it
        if len(numbers) == 1:
            return float(numbers[0])

        # Prefer the last number (typically the final answer, not a year or
        # context number). Filter out likely year values (1900-2099) unless
        # all numbers look like years.
        non_year = [n for n in numbers if not (1900 <= abs(float(n)) <= 2099 and '.' not in n)]
        if non_year:
            return float(non_year[-1])

        return float(numbers[-1])

    def _check_boolean(self, predicted: str, reference: str) -> bool:
        """Check boolean answer."""
        pred_lower = predicted.lower().strip()
        ref_lower = reference.lower().strip()

        true_values = {'true', 'yes', '1', 'correct'}
        false_values = {'false', 'no', '0', 'incorrect'}

        pred_bool = pred_lower in true_values
        ref_bool = ref_lower in true_values

        if pred_lower in true_values or pred_lower in false_values:
            return pred_bool == ref_bool

        return False

    def _check_text(self, predicted: str, reference: str) -> bool:
        """Check text/multiple choice answer."""
        # Clean and normalize
        pred_clean = self._normalize_answer(predicted)
        ref_clean = self._normalize_answer(reference)

        # Exact match
        if pred_clean == ref_clean:
            return True

        # Check if predicted contains the reference answer
        if ref_clean in pred_clean:
            return True

        # Check for option letter match (A, B, C, D)
        pred_letter = self._extract_option_letter(predicted)
        ref_letter = self._extract_option_letter(reference)
        if pred_letter and ref_letter:
            return pred_letter == ref_letter

        return False

    def _normalize_answer(self, answer: str) -> str:
        """Normalize answer text for comparison."""
        # Convert to lowercase
        answer = answer.lower().strip()

        # Remove common prefixes
        prefixes = ['the answer is', 'answer:', 'my answer is', 'i choose']
        for prefix in prefixes:
            if answer.startswith(prefix):
                answer = answer[len(prefix):].strip()

        # Remove punctuation at start/end
        answer = answer.strip('.,!?:;')

        # Normalize financial format variants:
        # +$38M / $+38M / $38M → canonical form $+38M
        # -$38M / $-38M → canonical form $-38M
        answer = re.sub(r'\+\$(\d)', r'$+\1', answer)
        answer = re.sub(r'-\$(\d)', r'$-\1', answer)

        return answer

    def _extract_option_letter(self, text: str) -> Optional[str]:
        """Extract option letter (A, B, C, D) from text."""
        # Look for standalone letter
        match = re.search(r'\b([A-Da-d])\b', text)
        if match:
            return match.group(1).upper()

        # Look for letter with punctuation
        match = re.search(r'^([A-Da-d])[.)\s:]', text)
        if match:
            return match.group(1).upper()

        return None

    def compute(self) -> EvaluationResults:
        """
        Compute all metrics from collected predictions.

        Returns:
            EvaluationResults with all computed metrics
        """
        if not self._predictions:
            return EvaluationResults(
                total_examples=0,
                overall_accuracy=0.0,
                category_accuracy={},
                difficulty_accuracy={},
            )

        # Overall accuracy
        correct = sum(1 for p in self._predictions if p.is_correct)
        total = len(self._predictions)
        overall_accuracy = correct / total

        # Category accuracy
        category_correct = defaultdict(int)
        category_total = defaultdict(int)
        for p in self._predictions:
            category_total[p.category] += 1
            if p.is_correct:
                category_correct[p.category] += 1

        category_accuracy = {
            cat: category_correct[cat] / category_total[cat]
            for cat in category_total
        }

        # Difficulty accuracy
        difficulty_correct = defaultdict(int)
        difficulty_total = defaultdict(int)
        for p in self._predictions:
            difficulty_total[p.difficulty] += 1
            if p.is_correct:
                difficulty_correct[p.difficulty] += 1

        difficulty_accuracy = {
            diff: difficulty_correct[diff] / difficulty_total[diff]
            for diff in difficulty_total
        }

        # Calibration metrics (if confidence scores available)
        calibration_error = None
        brier_score_avg = None
        log_loss_avg = None
        calibration_per_bin = None

        predictions_with_conf = [
            p for p in self._predictions if p.confidence is not None
        ]
        if predictions_with_conf:
            conf_probs = [p.confidence for p in predictions_with_conf]
            outcomes = [int(p.is_correct) for p in predictions_with_conf]

            # Use the calibration module for ECE with per-bin stats
            ece_val, bin_stats = expected_calibration_error(conf_probs, outcomes)
            calibration_error = ece_val
            calibration_per_bin = bin_stats

            # Compute Brier and log loss averages
            brier_scores = [
                brier_score(c, o) for c, o in zip(conf_probs, outcomes)
            ]
            log_losses = [
                log_loss_score(c, o) for c, o in zip(conf_probs, outcomes)
            ]
            brier_score_avg = round(
                sum(brier_scores) / len(brier_scores), 4
            )
            log_loss_avg = round(
                sum(log_losses) / len(log_losses), 4
            )

        # Reasoning quality from rubric scoring
        reasoning_quality = self._compute_reasoning_quality()

        return EvaluationResults(
            total_examples=total,
            overall_accuracy=overall_accuracy,
            category_accuracy=category_accuracy,
            difficulty_accuracy=difficulty_accuracy,
            reasoning_quality=reasoning_quality,
            calibration_error=calibration_error,
            brier_score_avg=brier_score_avg,
            log_loss_avg=log_loss_avg,
            calibration_per_bin=calibration_per_bin,
            correct_count=correct,
            predictions=self._predictions,
        )

    def _compute_reasoning_quality(
        self,
        use_llm: bool = False,
        llm_judge_model: str = "claude-opus-4-20250514",
        llm_judge_api_key: Optional[str] = None,
    ) -> Optional[float]:
        """
        Compute reasoning quality.

        When use_llm=False (default), evaluates model reasoning against key
        criteria from the PRBench-aligned rubric using heuristic keyword
        matching. Returns a 0-5 scale score.

        When use_llm=True, instantiates FinancialReasoningJudge and calls
        .grade() for each prediction that has reasoning. The LLM-graded
        criterion judgments are aggregated to a 0-5 scale score matching the
        heuristic output range. Fallback results (judge_validation_failure) are
        excluded from the average; if all results are fallbacks, returns None.

        Args:
            use_llm: If True, use AI-as-judge scoring instead of heuristics.
                     Default False for backwards compatibility.
            llm_judge_model: Anthropic model to use for judging (use_llm=True only).
            llm_judge_api_key: Optional API key override (use_llm=True only).
        """
        predictions_with_reasoning = [
            p for p in self._predictions if p.reasoning and len(p.reasoning) > 20
        ]
        if not predictions_with_reasoning:
            return None

        if use_llm:
            return self._compute_reasoning_quality_llm(
                predictions_with_reasoning,
                model=llm_judge_model,
                api_key=llm_judge_api_key,
            )

        total_score = 0.0

        for pred in predictions_with_reasoning:
            reasoning = pred.reasoning.lower()
            score = 0.0
            checks = 0

            # Numerical Accuracy: shows intermediate calculations
            if any(op in reasoning for op in ['=', '×', '÷', '/', '*', 'calculate']):
                score += 1.0
            checks += 1

            # Conceptual Understanding: identifies the core concept
            financial_concepts = [
                'margin', 'ratio', 'growth', 'dcf', 'ebitda', 'eps', 'revenue',
                'cash flow', 'working capital', 'leverage', 'coverage', 'valuation',
                'discount', 'terminal', 'wacc', 'roe', 'roic', 'dupont',
                'accrual', 'red flag', 'related party', 'earnings',
            ]
            if sum(1 for c in financial_concepts if c in reasoning) >= 2:
                score += 1.0
            checks += 1

            # Reasoning Chain: steps follow logical sequence
            step_markers = [
                'step 1', 'step 2', 'first', 'second', 'next', 'then',
                'therefore', 'thus', 'because', 'since', 'given that',
                '1.', '2.', '3.',
            ]
            if sum(1 for m in step_markers if m in reasoning) >= 2:
                score += 1.0
            checks += 1

            # Completeness: addresses the question with adequate detail
            if len(reasoning) > 100:
                score += 0.5
            if len(reasoning) > 300:
                score += 0.5
            checks += 1

            # Risk/Assumption Awareness: considers alternatives or caveats
            awareness_markers = [
                'however', 'although', 'risk', 'assumption', 'caveat',
                'note that', 'important', 'consider', 'alternatively',
                'potential', 'concern', 'limitation', 'may not', 'could',
            ]
            if any(m in reasoning for m in awareness_markers):
                score += 1.0
            checks += 1

            # Scale to 5.0
            total_score += (score / checks) * 5.0

        return round(total_score / len(predictions_with_reasoning), 2)

    def _compute_reasoning_quality_llm(
        self,
        predictions_with_reasoning: list[PredictionResult],
        model: str = "claude-opus-4-20250514",
        api_key: Optional[str] = None,
    ) -> Optional[float]:
        """LLM-as-judge path for reasoning quality scoring.

        Grades each prediction's reasoning using FinancialReasoningJudge against
        the default PRBench criteria set. Aggregates per-criterion judgments to a
        0-5 scale score matching the heuristic output range.

        Fallback results (judge_validation_failure) are excluded from the average.
        Returns None if all results are fallbacks.
        """
        from .ai_judge import FinancialReasoningJudge
        from .rubric_scoring import DEFAULT_CRITERIA

        judge = FinancialReasoningJudge(model=model, api_key=api_key)
        total_score = 0.0
        valid_count = 0

        for pred in predictions_with_reasoning:
            result = judge.grade(
                question=pred.problem_id,  # use problem_id as question placeholder
                context="",
                correct_answer=pred.correct_answer,
                model_response=pred.reasoning or "",
                criteria=DEFAULT_CRITERIA,
                problem_category=pred.category,
            )

            if result.fallback_used:
                continue

            # Convert binary judgments to a 0-5 score:
            # earned weighted points / total possible points * 5
            criterion_map = {c.id: c for c in DEFAULT_CRITERIA}
            earned = 0
            possible = 0
            for j in result.criterion_judgments:
                criterion = criterion_map.get(j.criterion_id)
                if criterion is None:
                    continue
                possible += criterion.weight
                if j.met:
                    earned += criterion.weight

            if possible > 0:
                total_score += (earned / possible) * 5.0
                valid_count += 1

        if valid_count == 0:
            return None

        return round(total_score / valid_count, 2)

    def _compute_calibration_error(self, n_bins: int = 10) -> float:
        """Compute Expected Calibration Error (ECE).

        Delegates to the calibration module's expected_calibration_error().
        Kept for backward compatibility. The compute() method now calls
        the calibration module directly for the richer per-bin version.

        Args:
            n_bins: Number of bins for calibration

        Returns:
            ECE score (lower is better)
        """
        predictions_with_conf = [
            p for p in self._predictions if p.confidence is not None
        ]

        if not predictions_with_conf:
            return 0.0

        conf_probs = [p.confidence for p in predictions_with_conf]
        outcomes = [int(p.is_correct) for p in predictions_with_conf]
        ece_val, _ = expected_calibration_error(conf_probs, outcomes, n_bins)
        return ece_val

    def reset(self):
        """Reset collected predictions."""
        self._predictions = []


def compute_accuracy(predictions: list[str], references: list[str]) -> float:
    """
    Compute simple accuracy.

    Args:
        predictions: List of predicted answers
        references: List of reference answers

    Returns:
        Accuracy score (0-1)
    """
    if not predictions or len(predictions) != len(references):
        return 0.0

    metrics = FinancialReasoningMetrics()
    for i, (pred, ref) in enumerate(zip(predictions, references)):
        metrics.add_prediction(
            problem_id=str(i),
            predicted=pred,
            reference=ref,
            category="unknown",
            difficulty="unknown",
        )

    results = metrics.compute()
    return results.overall_accuracy


def compute_category_accuracy(
    predictions: list[dict],
    references: list[dict],
) -> dict[str, float]:
    """
    Compute accuracy by category.

    Args:
        predictions: List of prediction dicts with 'id', 'predicted'
        references: List of reference dicts with 'id', 'correct_answer', 'category'

    Returns:
        Dictionary mapping category to accuracy
    """
    metrics = FinancialReasoningMetrics()
    metrics.add_batch(predictions, references)
    results = metrics.compute()
    return results.category_accuracy


def compute_difficulty_accuracy(
    predictions: list[dict],
    references: list[dict],
) -> dict[str, float]:
    """
    Compute accuracy by difficulty.

    Args:
        predictions: List of prediction dicts
        references: List of reference dicts with 'difficulty'

    Returns:
        Dictionary mapping difficulty to accuracy
    """
    metrics = FinancialReasoningMetrics()
    metrics.add_batch(predictions, references)
    results = metrics.compute()
    return results.difficulty_accuracy


def compute_reasoning_quality(
    predictions: list[dict],
    references: list[dict],
    rubric: Optional[dict] = None,
) -> float:
    """
    Compute reasoning quality score.

    This is a placeholder for more sophisticated reasoning evaluation
    that could use the rubrics from eval/llm_rubrics/.

    Args:
        predictions: List of prediction dicts with 'reasoning'
        references: List of reference dicts with 'reasoning_steps'
        rubric: Optional evaluation rubric

    Returns:
        Average reasoning quality score (1-5 scale)
    """
    # Basic implementation: check for key reasoning elements
    total_score = 0.0
    count = 0

    for pred, ref in zip(predictions, references):
        pred_reasoning = pred.get('reasoning', '')
        ref_steps = ref.get('reasoning_steps', [])

        if not pred_reasoning:
            continue

        # Score based on coverage of reference steps
        score = 0.0
        if ref_steps:
            steps_covered = sum(
                1 for step in ref_steps
                if any(word in pred_reasoning.lower() for word in step.lower().split())
            )
            score = min(5.0, 1.0 + (steps_covered / len(ref_steps)) * 4.0)
        else:
            # If no reference steps, give partial credit for any reasoning
            score = 3.0 if len(pred_reasoning) > 50 else 2.0

        total_score += score
        count += 1

    return total_score / count if count > 0 else 0.0
