"""
Anthropic Runner for Financial Reasoning Eval Benchmark

Supports Claude Opus 4, Claude Sonnet 4, and other Anthropic models.
"""

import os
import time
from typing import Optional

from .base import BaseRunner, RunnerConfig, ModelResponse, estimate_cost_usd

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def _format_system(system: str | None) -> list[dict] | str | None:
    """Wrap system prompts >= 400 chars with cache_control for prompt caching."""
    if not system or len(system) < 400:
        return system
    return [
        {
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }
    ]


class AnthropicRunner(BaseRunner):
    """Runner for Anthropic Claude models."""

    # Model aliases for convenience
    # Note: Some models may require specific API key permissions
    MODEL_ALIASES = {
        # Current generation (2025)
        "claude-opus-4": "claude-opus-4-20250514",
        "claude-sonnet-4": "claude-sonnet-4-20250514",
        "claude-haiku-3.5": "claude-3-5-haiku-20241022",
        # Previous generation
        "claude-3.5-sonnet": "claude-3-5-sonnet-20241022",
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
        # Short aliases
        "claude-opus": "claude-opus-4-20250514",
        "claude-sonnet": "claude-sonnet-4-20250514",
        "claude-haiku": "claude-3-5-haiku-20241022",
    }

    def __init__(self, config: RunnerConfig):
        """
        Initialize the Anthropic runner.

        Args:
            config: Runner configuration
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

        super().__init__(config)

        # Get API key
        api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key in config."
            )

        # Initialize client
        client_kwargs = {"api_key": api_key}
        if config.api_base:
            client_kwargs["base_url"] = config.api_base

        self.client = anthropic.Anthropic(**client_kwargs)

        # Resolve model alias
        self.model = self.MODEL_ALIASES.get(
            config.model_name.lower(),
            config.model_name
        )

    def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response using Anthropic's API.

        Args:
            prompt: The input prompt

        Returns:
            ModelResponse with the model's output
        """
        start_time = time.time()

        try:
            # Build request parameters
            request_params = {
                "model": self.model,
                "max_tokens": self.config.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }

            # Add system prompt if provided
            if self.config.system_prompt:
                request_params["system"] = _format_system(self.config.system_prompt)

            # Add optional parameters
            if self.config.temperature > 0:
                request_params["temperature"] = self.config.temperature

            if self.config.top_p < 1.0:
                request_params["top_p"] = self.config.top_p

            if self.config.stop_sequences:
                request_params["stop_sequences"] = self.config.stop_sequences

            # Make the API call
            response = self.client.messages.create(**request_params)

            # Extract response
            latency_ms = (time.time() - start_time) * 1000

            # Get text content
            full_response = ""
            for block in response.content:
                if block.type == "text":
                    full_response += block.text

            # Parse answer and reasoning
            answer, reasoning = self.parse_response(full_response)

            # Get token usage
            tokens_used = 0
            input_tokens = 0
            output_tokens = 0
            if response.usage:
                input_tokens = int(getattr(response.usage, "input_tokens", 0) or 0)
                output_tokens = int(getattr(response.usage, "output_tokens", 0) or 0)
                tokens_used = input_tokens + output_tokens

            cost_usd = estimate_cost_usd(self.model, input_tokens, output_tokens)
            wall_time_s = latency_ms / 1000.0

            return ModelResponse(
                answer=answer,
                reasoning=reasoning,
                full_response=full_response,
                model=self.model,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                wall_time_s=wall_time_s,
                cost_usd=cost_usd,
                success=True,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ModelResponse(
                answer="",
                full_response="",
                model=self.model,
                latency_ms=latency_ms,
                error=str(e),
                success=False,
            )

    def generate_with_thinking(
        self,
        prompt: str,
        max_tokens: int = 16384,
        system: Optional[str] = None,
        thinking_budget: int = 8000,
    ) -> ModelResponse:
        """
        Generate a response using Anthropic's extended thinking API.

        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens for the response (must exceed thinking_budget)
            system: Optional system prompt override
            thinking_budget: Token budget for the thinking phase

        Returns:
            ModelResponse with reasoning from extended thinking
        """
        start_time = time.time()

        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": messages,
                "thinking": {
                    "type": "enabled",
                    "budget_tokens": thinking_budget,
                },
            }
            # Ensure max_tokens accommodates thinking budget
            if kwargs["max_tokens"] < thinking_budget + 1024:
                kwargs["max_tokens"] = thinking_budget + 4096
            if system:
                kwargs["system"] = _format_system(system)
            elif self.config.system_prompt:
                kwargs["system"] = _format_system(self.config.system_prompt)

            response = self.client.messages.create(**kwargs)

            latency_ms = (time.time() - start_time) * 1000

            thinking_text = ""
            answer_text = ""
            for block in response.content:
                if block.type == "thinking":
                    thinking_text = block.thinking
                elif block.type == "text":
                    answer_text = block.text

            tokens_used = 0
            input_tokens = 0
            output_tokens = 0
            if response.usage:
                input_tokens = int(getattr(response.usage, "input_tokens", 0) or 0)
                output_tokens = int(getattr(response.usage, "output_tokens", 0) or 0)
                tokens_used = input_tokens + output_tokens

            cost_usd = estimate_cost_usd(self.model, input_tokens, output_tokens)
            wall_time_s = latency_ms / 1000.0

            return ModelResponse(
                answer=answer_text,
                reasoning=thinking_text,
                full_response=answer_text,
                model=self.model,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                wall_time_s=wall_time_s,
                cost_usd=cost_usd,
                success=True,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ModelResponse(
                answer="",
                full_response="",
                model=self.model,
                latency_ms=latency_ms,
                error=str(e),
                success=False,
            )


def create_anthropic_runner(
    model: str = "claude-sonnet-4",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> AnthropicRunner:
    """
    Create an Anthropic runner with common defaults.

    Args:
        model: Model name (claude-opus-4, claude-sonnet-4, claude-haiku-3.5, etc.)
        api_key: Optional API key (defaults to ANTHROPIC_API_KEY env var)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        Configured AnthropicRunner
    """
    config = RunnerConfig(
        model_name=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=(
            "You are a financial analyst with expertise in evaluating financial models, "
            "analyzing earnings, and assessing investment opportunities. "
            "Provide clear, well-reasoned answers to financial questions. "
            "Always show your reasoning step by step before providing your final answer."
        ),
    )
    return AnthropicRunner(config)
