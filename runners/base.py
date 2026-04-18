"""
Base Runner for LLM Evaluation

Provides the abstract interface for running LLMs on the benchmark.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Iterator
import time


@dataclass
class RunnerConfig:
    """Configuration for LLM runners."""

    # Model identification
    model_name: str
    model_version: Optional[str] = None

    # Generation parameters
    max_tokens: int = 1024
    temperature: float = 0.0
    top_p: float = 1.0
    stop_sequences: list[str] = field(default_factory=list)

    # API configuration
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    timeout: int = 60

    # Batch processing
    batch_size: int = 1
    max_retries: int = 3
    retry_delay: float = 1.0

    # Prompt configuration
    system_prompt: Optional[str] = None
    include_options: bool = True
    include_reasoning_request: bool = True


# Per-1M token pricing table (USD). Numbers are approximate list prices
# as of 2026-Q1 and are used only for informational leaderboard cost
# columns. Providers drift; update before a public leaderboard push.
# Format: model_id -> {"input": $/1M in-tokens, "output": $/1M out-tokens}.
PRICING_PER_1M_USD: dict[str, dict[str, float]] = {
    # Anthropic — current
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.0},
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    # OpenAI — current
    "gpt-4.1": {"input": 2.0, "output": 8.0},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "gpt-4o": {"input": 2.50, "output": 10.0},
    "o3": {"input": 10.0, "output": 40.0},
    "o3-mini": {"input": 1.10, "output": 4.40},
    "o4-mini": {"input": 1.10, "output": 4.40},
    "o1": {"input": 15.0, "output": 60.0},
    # Open weights / hosted
    "deepseek-v3.1": {"input": 0.27, "output": 1.10},
    "llama-3.3-70b": {"input": 0.90, "output": 0.90},
    "qwen3.5-122b-a10b": {"input": 0.0, "output": 0.0},  # local Ollama
}


def estimate_cost_usd(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> Optional[float]:
    """Return USD cost estimate for a single call, or None if unknown.

    Lookup is substring-based so that versioned SKUs (e.g.
    ``claude-sonnet-4-20250514``) match both exact and shortform entries.
    """
    if not model_name:
        return None
    key = model_name.lower()
    pricing = PRICING_PER_1M_USD.get(key)
    if pricing is None:
        # Try a shortform lookup (e.g. "claude-sonnet-4" in the full SKU).
        for candidate, price in PRICING_PER_1M_USD.items():
            if candidate in key or key in candidate:
                pricing = price
                break
    if pricing is None:
        return None
    return round(
        input_tokens * pricing["input"] / 1_000_000
        + output_tokens * pricing["output"] / 1_000_000,
        6,
    )


@dataclass
class ModelResponse:
    """Response from an LLM."""

    # Core response
    answer: str
    reasoning: Optional[str] = None
    full_response: str = ""

    # Metadata
    model: str = ""
    latency_ms: float = 0.0
    tokens_used: int = 0
    confidence: Optional[float] = None

    # Fine-grained token + cost tracking (optional; filled by runners
    # that report usage. Absent values stay None/0 so older call sites
    # continue to work.)
    input_tokens: int = 0
    output_tokens: int = 0
    wall_time_s: float = 0.0
    cost_usd: Optional[float] = None

    # Error handling
    error: Optional[str] = None
    success: bool = True

    def extract_answer(self) -> str:
        """Extract the final answer from the response."""
        # Try to find answer in common formats
        text = self.full_response.lower()

        # Look for explicit answer markers
        answer_markers = [
            "the answer is",
            "my answer is",
            "i choose",
            "correct answer:",
            "answer:",
        ]

        for marker in answer_markers:
            if marker in text:
                idx = text.index(marker) + len(marker)
                answer_text = self.full_response[idx:].strip()
                # Get first line or first sentence
                first_line = answer_text.split('\n')[0].strip()
                return first_line

        # Return the stored answer if extraction fails
        return self.answer


class BaseRunner(ABC):
    """Abstract base class for LLM runners."""

    def __init__(self, config: RunnerConfig):
        """
        Initialize the runner.

        Args:
            config: Runner configuration
        """
        self.config = config
        self._validate_config()

    def _validate_config(self):
        """Validate the configuration."""
        if not self.config.model_name:
            raise ValueError("model_name is required in RunnerConfig")

    @abstractmethod
    def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response for a single prompt.

        Args:
            prompt: The input prompt

        Returns:
            ModelResponse with the model's output
        """
        pass

    def generate_batch(
        self,
        prompts: list[str],
        show_progress: bool = True,
    ) -> list[ModelResponse]:
        """
        Generate responses for a batch of prompts.

        Args:
            prompts: List of input prompts
            show_progress: Whether to show progress

        Returns:
            List of ModelResponse objects
        """
        responses = []
        total = len(prompts)

        for i, prompt in enumerate(prompts):
            if show_progress:
                print(f"Processing {i + 1}/{total}...", end='\r')

            response = self._generate_with_retry(prompt)
            responses.append(response)

        if show_progress:
            print(f"Completed {total}/{total} prompts")

        return responses

    def _generate_with_retry(self, prompt: str) -> ModelResponse:
        """Generate with retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                return self.generate(prompt)
            except Exception as e:
                last_error = str(e)
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))

        return ModelResponse(
            answer="",
            full_response="",
            model=self.config.model_name,
            error=f"Failed after {self.config.max_retries} attempts: {last_error}",
            success=False,
        )

    def format_prompt(
        self,
        question: str,
        context: str,
        options: Optional[list[dict]] = None,
    ) -> str:
        """
        Format a benchmark question as a prompt.

        Args:
            question: The question text
            context: Financial context
            options: Answer options (for multiple choice)

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        # Add system instruction
        if self.config.system_prompt:
            prompt_parts.append(self.config.system_prompt)
            prompt_parts.append("")

        # Add context
        if context:
            prompt_parts.append("## Context")
            prompt_parts.append(context)
            prompt_parts.append("")

        # Add question
        prompt_parts.append("## Question")
        prompt_parts.append(question)

        # Add options
        if self.config.include_options and options:
            prompt_parts.append("")
            prompt_parts.append("## Options")
            for opt in options:
                prompt_parts.append(f"{opt.get('id', '')}. {opt.get('text', '')}")

        # Add reasoning request
        if self.config.include_reasoning_request:
            prompt_parts.append("")
            prompt_parts.append("Please provide your answer and explain your reasoning step by step.")
            prompt_parts.append("Format your response as:")
            prompt_parts.append("Reasoning: [Your step-by-step analysis]")
            if not options:
                prompt_parts.append("Answer: [A single number or short phrase — no sentences]")
            else:
                prompt_parts.append("Answer: [Your final answer]")

        return "\n".join(prompt_parts)

    def parse_response(self, response_text: str) -> tuple[str, Optional[str]]:
        """
        Parse a model response to extract answer and reasoning.

        Args:
            response_text: Raw response from the model

        Returns:
            Tuple of (answer, reasoning)
        """
        answer = ""
        reasoning = None

        lines = response_text.strip().split('\n')

        # Look for structured response
        reasoning_lines = []
        answer_lines = []
        in_reasoning = False
        in_answer = False

        for line in lines:
            line_lower = line.lower().strip()

            if line_lower.startswith('reasoning:'):
                in_reasoning = True
                in_answer = False
                content = line[len('reasoning:'):].strip()
                if content:
                    reasoning_lines.append(content)
            elif line_lower.startswith('answer:'):
                in_answer = True
                in_reasoning = False
                content = line[len('answer:'):].strip()
                if content:
                    answer_lines.append(content)
            elif in_reasoning:
                reasoning_lines.append(line)
            elif in_answer:
                answer_lines.append(line)

        if answer_lines:
            answer = '\n'.join(answer_lines).strip()

        if reasoning_lines:
            reasoning = '\n'.join(reasoning_lines).strip()

        # Fallback: if no structured response, use the whole thing
        if not answer:
            # Try to find the answer in common formats
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith('#'):
                    answer = line
                    break

        return answer, reasoning

    @property
    def model_identifier(self) -> str:
        """Get a unique identifier for the model."""
        if self.config.model_version:
            return f"{self.config.model_name}:{self.config.model_version}"
        return self.config.model_name
