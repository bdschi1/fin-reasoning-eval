"""
Leaderboard System for Financial Reasoning Eval Benchmark

Manages model rankings, scores, and historical tracking.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from pathlib import Path


@dataclass
class LeaderboardEntry:
    """A single entry on the leaderboard."""

    # Model identification
    model_name: str
    model_version: Optional[str] = None
    organization: Optional[str] = None

    # Overall metrics
    overall_accuracy: float = 0.0
    total_examples: int = 0

    # Category breakdown
    category_accuracy: dict[str, float] = field(default_factory=dict)

    # Difficulty breakdown
    difficulty_accuracy: dict[str, float] = field(default_factory=dict)

    # Additional metrics
    reasoning_quality: Optional[float] = None
    calibration_error: Optional[float] = None
    avg_latency_ms: Optional[float] = None

    # Metadata
    submission_date: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    submitted_by: Optional[str] = None
    notes: Optional[str] = None

    # Ranking
    rank: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'LeaderboardEntry':
        """Create from dictionary."""
        return cls(**data)

    @property
    def display_name(self) -> str:
        """Get display name for the entry."""
        if self.organization:
            return f"{self.organization}/{self.model_name}"
        return self.model_name


class Leaderboard:
    """
    Manages the benchmark leaderboard.

    Stores entries, computes rankings, and provides display utilities.
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the leaderboard.

        Args:
            storage_path: Path to store leaderboard data
        """
        self.storage_path = storage_path or self._default_storage_path()
        self.entries: list[LeaderboardEntry] = []
        self._load()

    def _default_storage_path(self) -> str:
        """Get default storage path."""
        return str(Path(__file__).parent.parent / "data" / "leaderboard.json")

    def _load(self):
        """Load leaderboard from storage."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.entries = [LeaderboardEntry.from_dict(e) for e in data.get('entries', [])]
        self._update_ranks()

    def _save(self):
        """Save leaderboard to storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            'updated_at': datetime.utcnow().isoformat(),
            'total_entries': len(self.entries),
            'entries': [e.to_dict() for e in self.entries],
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _update_ranks(self):
        """Update rankings based on overall accuracy."""
        # Sort by overall accuracy (descending)
        self.entries.sort(key=lambda e: e.overall_accuracy, reverse=True)

        # Assign ranks
        for i, entry in enumerate(self.entries):
            entry.rank = i + 1

    def add_entry(self, entry: LeaderboardEntry) -> int:
        """
        Add a new entry to the leaderboard.

        Args:
            entry: LeaderboardEntry to add

        Returns:
            Rank of the new entry
        """
        # Check for existing entry with same model
        existing_idx = None
        for i, existing in enumerate(self.entries):
            if (existing.model_name == entry.model_name and
                existing.model_version == entry.model_version):
                existing_idx = i
                break

        if existing_idx is not None:
            # Update existing entry if new score is better
            if entry.overall_accuracy > self.entries[existing_idx].overall_accuracy:
                self.entries[existing_idx] = entry
        else:
            self.entries.append(entry)

        self._update_ranks()
        self._save()

        return entry.rank

    def get_entry(self, model_name: str, model_version: Optional[str] = None) -> Optional[LeaderboardEntry]:
        """Get a specific entry."""
        for entry in self.entries:
            if entry.model_name == model_name:
                if model_version is None or entry.model_version == model_version:
                    return entry
        return None

    def get_top_n(self, n: int = 10) -> list[LeaderboardEntry]:
        """Get top N entries."""
        return self.entries[:n]

    def get_by_category(self, category: str) -> list[tuple[LeaderboardEntry, float]]:
        """Get entries sorted by performance on a specific category."""
        entries_with_score = [
            (e, e.category_accuracy.get(category, 0))
            for e in self.entries
        ]
        entries_with_score.sort(key=lambda x: x[1], reverse=True)
        return entries_with_score

    def get_by_difficulty(self, difficulty: str) -> list[tuple[LeaderboardEntry, float]]:
        """Get entries sorted by performance on a specific difficulty."""
        entries_with_score = [
            (e, e.difficulty_accuracy.get(difficulty, 0))
            for e in self.entries
        ]
        entries_with_score.sort(key=lambda x: x[1], reverse=True)
        return entries_with_score

    def to_markdown_table(self, n: int = 20) -> str:
        """
        Generate a markdown table of the leaderboard.

        Args:
            n: Number of entries to include

        Returns:
            Markdown formatted table
        """
        entries = self.get_top_n(n)

        if not entries:
            return "No entries yet."

        # Header
        lines = [
            "| Rank | Model | Overall | Easy | Medium | Hard | Expert |",
            "|------|-------|---------|------|--------|------|--------|",
        ]

        # Rows
        for entry in entries:
            easy = entry.difficulty_accuracy.get('easy', 0)
            medium = entry.difficulty_accuracy.get('medium', 0)
            hard = entry.difficulty_accuracy.get('hard', 0)
            expert = entry.difficulty_accuracy.get('expert', 0)

            lines.append(
                f"| {entry.rank} | {entry.display_name} | "
                f"{entry.overall_accuracy:.1%} | "
                f"{easy:.1%} | {medium:.1%} | {hard:.1%} | {expert:.1%} |"
            )

        return "\n".join(lines)

    def to_category_table(self, n: int = 20) -> str:
        """Generate a markdown table showing category breakdown."""
        entries = self.get_top_n(n)

        if not entries:
            return "No entries yet."

        # Get all categories
        all_categories = set()
        for entry in entries:
            all_categories.update(entry.category_accuracy.keys())
        categories = sorted(all_categories)

        # Header
        header = "| Rank | Model |" + " | ".join(c[:12] for c in categories) + " |"
        separator = "|------|-------|" + " | ".join("----" for _ in categories) + " |"

        lines = [header, separator]

        # Rows
        for entry in entries:
            row = f"| {entry.rank} | {entry.display_name} |"
            for cat in categories:
                acc = entry.category_accuracy.get(cat, 0)
                row += f" {acc:.0%} |"
            lines.append(row)

        return "\n".join(lines)

    def generate_report(self) -> str:
        """Generate a full leaderboard report."""
        lines = [
            "# Financial Reasoning Eval Benchmark Leaderboard",
            "",
            f"*Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*",
            "",
            "## Overall Rankings",
            "",
            self.to_markdown_table(),
            "",
            "## Category Performance",
            "",
            self.to_category_table(),
            "",
            "## Statistics",
            "",
            f"- Total submissions: {len(self.entries)}",
        ]

        if self.entries:
            avg_acc = sum(e.overall_accuracy for e in self.entries) / len(self.entries)
            best_entry = self.entries[0]
            lines.extend([
                f"- Average accuracy: {avg_acc:.1%}",
                f"- Best performing model: {best_entry.display_name} ({best_entry.overall_accuracy:.1%})",
            ])

        return "\n".join(lines)


def create_entry_from_results(results: dict, model_name: Optional[str] = None) -> LeaderboardEntry:
    """
    Create a leaderboard entry from evaluation results.

    Args:
        results: Results dictionary from evaluation
        model_name: Optional model name override

    Returns:
        LeaderboardEntry
    """
    metrics = results.get('metrics', {})

    return LeaderboardEntry(
        model_name=model_name or results.get('model', 'Unknown'),
        overall_accuracy=metrics.get('overall_accuracy', 0.0),
        total_examples=metrics.get('total_examples', 0),
        category_accuracy=metrics.get('category_accuracy', {}),
        difficulty_accuracy=metrics.get('difficulty_accuracy', {}),
        reasoning_quality=metrics.get('reasoning_quality'),
        calibration_error=metrics.get('calibration_error'),
    )
