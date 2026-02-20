"""
HuggingFace Dataset Integration for Financial Reasoning Eval Benchmark

Provides loading and processing utilities compatible with the
HuggingFace datasets library.
"""

import json
import os
from pathlib import Path
from typing import Optional, Union, Iterator
from dataclasses import dataclass

try:
    from datasets import Dataset, DatasetDict, Features, Value, Sequence
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    Dataset = None
    DatasetDict = None


@dataclass
class FinancialReasoningExample:
    """A single example from the benchmark."""
    id: str
    category: str
    difficulty: str
    question: str
    context: str
    answer_type: str
    correct_answer: str
    options: list[dict]
    explanation: str
    reasoning_steps: list[str]
    tags: list[str]

    def format_for_llm(self, include_options: bool = True) -> str:
        """Format the example as a prompt for LLM evaluation."""
        prompt_parts = [
            self.context,
            "",
            "Question:",
            self.question,
        ]

        if include_options and self.options:
            prompt_parts.append("")
            prompt_parts.append("Options:")
            for opt in self.options:
                prompt_parts.append(f"  {opt['id']}. {opt['text']}")

        prompt_parts.extend([
            "",
            "Please provide your answer and reasoning."
        ])

        return "\n".join(prompt_parts)


class FinancialReasoningDataset:
    """
    Dataset wrapper for the Financial Reasoning Eval Benchmark.

    Supports both native Python iteration and HuggingFace datasets integration.
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        split: str = "test",
        categories: Optional[list[str]] = None,
        difficulties: Optional[list[str]] = None,
    ):
        """
        Initialize the dataset.

        Args:
            data_dir: Directory containing the benchmark data files
            split: Dataset split to load ('test', 'validation')
            categories: Filter to specific problem categories
            difficulties: Filter to specific difficulty levels
        """
        self.data_dir = data_dir or self._find_data_dir()
        self.split = split
        self.categories = categories
        self.difficulties = difficulties

        self._examples: list[FinancialReasoningExample] = []
        self._load_data()

    def _find_data_dir(self) -> str:
        """Find the data directory relative to this file."""
        current_dir = Path(__file__).parent
        data_dir = current_dir.parent / "data"

        # Check for HuggingFace format first
        hf_dir = data_dir / "huggingface"
        if hf_dir.exists():
            return str(hf_dir)

        return str(data_dir)

    def _load_data(self):
        """Load data from files."""
        # Try JSONL format first (HuggingFace format)
        jsonl_path = os.path.join(self.data_dir, f"{self.split}.jsonl")
        if os.path.exists(jsonl_path):
            self._load_jsonl(jsonl_path)
            return

        # Try JSON format
        json_path = os.path.join(self.data_dir, f"benchmark_{self.split}.json")
        if os.path.exists(json_path):
            self._load_json(json_path)
            return

        # Try the full benchmark file
        full_path = os.path.join(self.data_dir, "financial_reasoning_benchmark.json")
        if os.path.exists(full_path):
            self._load_json(full_path)
            return

        raise FileNotFoundError(
            f"No benchmark data found in {self.data_dir}. "
            f"Run 'python benchmark/scripts/generate_dataset.py' first."
        )

    def _load_jsonl(self, filepath: str):
        """Load from JSONL format."""
        with open(filepath, 'r') as f:
            for line in f:
                record = json.loads(line)
                example = self._record_to_example(record)
                if self._should_include(example):
                    self._examples.append(example)

    def _load_json(self, filepath: str):
        """Load from JSON format."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        problems = data.get('problems', data) if isinstance(data, dict) else data

        for problem in problems:
            # Handle both flat and nested formats
            if 'context' in problem and isinstance(problem['context'], dict):
                # Nested format from ProblemSet
                context_str = self._format_context(problem['context'])
            else:
                context_str = problem.get('context', '')

            record = {
                'id': problem.get('id', ''),
                'category': problem.get('category', ''),
                'difficulty': problem.get('difficulty', ''),
                'question': problem.get('question', ''),
                'context': context_str,
                'answer_type': problem.get('answer_type', ''),
                'correct_answer': problem.get('correct_answer', ''),
                'options': problem.get('answer_options', []),
                'explanation': problem.get('explanation', ''),
                'reasoning_steps': problem.get('reasoning_steps', []),
                'tags': problem.get('tags', []),
            }
            example = self._record_to_example(record)
            if self._should_include(example):
                self._examples.append(example)

    def _format_context(self, context: dict) -> str:
        """Format context dictionary as string."""
        parts = []
        if context.get('company_name'):
            parts.append(f"Company: {context['company_name']}")
        if context.get('ticker'):
            parts.append(f"Ticker: {context['ticker']}")
        if context.get('sector'):
            parts.append(f"Sector: {context['sector']}")
        if context.get('revenue'):
            parts.append(f"Revenue: {context['revenue']}")
        if context.get('eps'):
            parts.append(f"EPS: {context['eps']}")
        if context.get('model_assumptions'):
            parts.append(f"Assumptions: {context['model_assumptions']}")
        if context.get('formula_context'):
            parts.append(f"Formula: {context['formula_context']}")
        return "\n".join(parts)

    def _record_to_example(self, record: dict) -> FinancialReasoningExample:
        """Convert a record to FinancialReasoningExample."""
        return FinancialReasoningExample(
            id=record.get('id', ''),
            category=record.get('category', ''),
            difficulty=record.get('difficulty', ''),
            question=record.get('question', ''),
            context=record.get('context', ''),
            answer_type=record.get('answer_type', ''),
            correct_answer=record.get('correct_answer', ''),
            options=record.get('options', []),
            explanation=record.get('explanation', ''),
            reasoning_steps=record.get('reasoning_steps', []),
            tags=record.get('tags', []),
        )

    def _should_include(self, example: FinancialReasoningExample) -> bool:
        """Check if example should be included based on filters."""
        if self.categories and example.category not in self.categories:
            return False
        if self.difficulties and example.difficulty not in self.difficulties:
            return False
        return True

    def __len__(self) -> int:
        return len(self._examples)

    def __iter__(self) -> Iterator[FinancialReasoningExample]:
        return iter(self._examples)

    def __getitem__(self, idx: int) -> FinancialReasoningExample:
        return self._examples[idx]

    def to_huggingface(self) -> 'Dataset':
        """
        Convert to HuggingFace Dataset format.

        Returns:
            HuggingFace Dataset object
        """
        if not HF_AVAILABLE:
            raise ImportError(
                "HuggingFace datasets library not installed. "
                "Install with: pip install datasets"
            )

        records = []
        for example in self._examples:
            records.append({
                'id': example.id,
                'category': example.category,
                'difficulty': example.difficulty,
                'question': example.question,
                'context': example.context,
                'answer_type': example.answer_type,
                'correct_answer': example.correct_answer,
                'options': json.dumps(example.options),
                'explanation': example.explanation,
                'reasoning_steps': example.reasoning_steps,
                'tags': example.tags,
            })

        return Dataset.from_list(records)

    def get_statistics(self) -> dict:
        """Get dataset statistics."""
        category_counts = {}
        difficulty_counts = {}

        for example in self._examples:
            category_counts[example.category] = category_counts.get(example.category, 0) + 1
            difficulty_counts[example.difficulty] = difficulty_counts.get(example.difficulty, 0) + 1

        return {
            'total_examples': len(self._examples),
            'category_distribution': category_counts,
            'difficulty_distribution': difficulty_counts,
        }


def load_benchmark(
    split: str = "test",
    data_dir: Optional[str] = None,
    categories: Optional[list[str]] = None,
    difficulties: Optional[list[str]] = None,
    as_huggingface: bool = False,
) -> Union[FinancialReasoningDataset, 'Dataset']:
    """
    Load the Financial Reasoning Eval Benchmark.

    Args:
        split: Dataset split ('test', 'validation')
        data_dir: Optional custom data directory
        categories: Filter to specific problem categories
        difficulties: Filter to specific difficulty levels
        as_huggingface: Return as HuggingFace Dataset

    Returns:
        FinancialReasoningDataset or HuggingFace Dataset
    """
    dataset = FinancialReasoningDataset(
        data_dir=data_dir,
        split=split,
        categories=categories,
        difficulties=difficulties,
    )

    if as_huggingface:
        return dataset.to_huggingface()

    return dataset


def load_benchmark_dict(
    data_dir: Optional[str] = None,
    as_huggingface: bool = False,
) -> Union[dict, 'DatasetDict']:
    """
    Load all benchmark splits as a dictionary.

    Args:
        data_dir: Optional custom data directory
        as_huggingface: Return as HuggingFace DatasetDict

    Returns:
        Dictionary of splits or HuggingFace DatasetDict
    """
    splits = {}

    for split in ['test', 'validation']:
        try:
            dataset = load_benchmark(
                split=split,
                data_dir=data_dir,
                as_huggingface=as_huggingface,
            )
            splits[split] = dataset
        except FileNotFoundError:
            continue

    if as_huggingface and HF_AVAILABLE:
        return DatasetDict(splits)

    return splits
