"""
Submission Handler for Financial Reasoning Eval Benchmark

Handles validation and processing of benchmark submissions.
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pathlib import Path

from .leaderboard import Leaderboard, LeaderboardEntry, create_entry_from_results


@dataclass
class SubmissionResult:
    """Result of a submission attempt."""
    success: bool
    message: str
    entry: Optional[LeaderboardEntry] = None
    rank: Optional[int] = None
    errors: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class SubmissionHandler:
    """
    Handles benchmark submissions.

    Validates submissions and adds them to the leaderboard.
    """

    REQUIRED_FIELDS = ['model', 'metrics']
    REQUIRED_METRICS = ['overall_accuracy', 'total_examples']

    def __init__(self, leaderboard: Optional[Leaderboard] = None):
        """
        Initialize the submission handler.

        Args:
            leaderboard: Leaderboard instance (creates new if not provided)
        """
        self.leaderboard = leaderboard or Leaderboard()

    def validate_submission(self, submission: dict) -> tuple[bool, list[str]]:
        """
        Validate a submission.

        Args:
            submission: Submission dictionary

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in submission:
                errors.append(f"Missing required field: {field}")

        if 'metrics' in submission:
            metrics = submission['metrics']
            for metric in self.REQUIRED_METRICS:
                if metric not in metrics:
                    errors.append(f"Missing required metric: {metric}")

            # Validate metric values
            accuracy = metrics.get('overall_accuracy', 0)
            if not (0 <= accuracy <= 1):
                errors.append(f"Invalid overall_accuracy: {accuracy} (must be 0-1)")

            total = metrics.get('total_examples', 0)
            if total <= 0:
                errors.append(f"Invalid total_examples: {total} (must be > 0)")

        return len(errors) == 0, errors

    def process_submission(
        self,
        submission: dict,
        submitted_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> SubmissionResult:
        """
        Process a benchmark submission.

        Args:
            submission: Submission dictionary with model and metrics
            submitted_by: Optional submitter name
            notes: Optional submission notes

        Returns:
            SubmissionResult with outcome
        """
        # Validate
        is_valid, errors = self.validate_submission(submission)
        if not is_valid:
            return SubmissionResult(
                success=False,
                message="Submission validation failed",
                errors=errors,
            )

        try:
            # Create entry
            entry = create_entry_from_results(submission)
            entry.submitted_by = submitted_by
            entry.notes = notes

            # Add to leaderboard
            rank = self.leaderboard.add_entry(entry)

            return SubmissionResult(
                success=True,
                message=f"Submission accepted! Model ranked #{rank}",
                entry=entry,
                rank=rank,
            )

        except Exception as e:
            return SubmissionResult(
                success=False,
                message=f"Error processing submission: {str(e)}",
                errors=[str(e)],
            )

    def process_file(
        self,
        filepath: str,
        submitted_by: Optional[str] = None,
    ) -> SubmissionResult:
        """
        Process a submission from a file.

        Args:
            filepath: Path to submission JSON file
            submitted_by: Optional submitter name

        Returns:
            SubmissionResult with outcome
        """
        if not os.path.exists(filepath):
            return SubmissionResult(
                success=False,
                message=f"File not found: {filepath}",
                errors=[f"File not found: {filepath}"],
            )

        try:
            with open(filepath, 'r') as f:
                submission = json.load(f)
        except json.JSONDecodeError as e:
            return SubmissionResult(
                success=False,
                message=f"Invalid JSON: {str(e)}",
                errors=[f"Invalid JSON: {str(e)}"],
            )

        return self.process_submission(
            submission,
            submitted_by=submitted_by,
            notes=f"Submitted from file: {filepath}",
        )


def submit_results(
    results_path: str,
    leaderboard_path: Optional[str] = None,
    submitted_by: Optional[str] = None,
) -> SubmissionResult:
    """
    Submit evaluation results to the leaderboard.

    Args:
        results_path: Path to results JSON file
        leaderboard_path: Optional custom leaderboard path
        submitted_by: Optional submitter name

    Returns:
        SubmissionResult
    """
    leaderboard = Leaderboard(storage_path=leaderboard_path) if leaderboard_path else Leaderboard()
    handler = SubmissionHandler(leaderboard)
    return handler.process_file(results_path, submitted_by)
