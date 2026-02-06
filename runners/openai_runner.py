"""
OpenAI Runner for Financial Reasoning Eval Benchmark

Supports GPT-4.1, o3, o4-mini, GPT-4o, and other OpenAI models.
"""

import os
import time
from typing import Optional

from .base import BaseRunner, RunnerConfig, ModelResponse

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIRunner(BaseRunner):
    """Runner for OpenAI models (GPT-4.1, o3, o4-mini, GPT-4o, etc.)."""

    # Model aliases for convenience
    MODEL_ALIASES = {
        # Current generation (2025)
        "gpt-4.1": "gpt-4.1-2025-04-14",
        "gpt-4.1-mini": "gpt-4.1-mini-2025-04-14",
        "gpt-4.1-nano": "gpt-4.1-nano-2025-04-14",
        "o3": "o3-2025-04-16",
        "o3-mini": "o3-mini-2025-01-31",
        "o4-mini": "o4-mini-2025-04-16",
        # Previous generation
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4-turbo": "gpt-4-turbo",
        "o1": "o1",
        "o1-mini": "o1-mini",
        # Legacy
        "gpt-4": "gpt-4",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
    }

    def __init__(self, config: RunnerConfig):
        """
        Initialize the OpenAI runner.

        Args:
            config: Runner configuration
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            )

        super().__init__(config)

        # Get API key
        api_key = config.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key in config."
            )

        # Initialize client
        client_kwargs = {"api_key": api_key}
        if config.api_base:
            client_kwargs["base_url"] = config.api_base

        self.client = openai.OpenAI(**client_kwargs)

        # Resolve model alias
        self.model = self.MODEL_ALIASES.get(
            config.model_name.lower(),
            config.model_name
        )

    @property
    def _is_reasoning_model(self) -> bool:
        """Check if the current model is a reasoning model (o-series)."""
        model_lower = self.model.lower()
        return model_lower.startswith("o1") or model_lower.startswith("o3") or model_lower.startswith("o4")

    def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response using OpenAI's API.

        Args:
            prompt: The input prompt

        Returns:
            ModelResponse with the model's output
        """
        start_time = time.time()

        try:
            # Build messages — reasoning models (o-series) use "developer"
            # role instead of "system" and don't support temperature/top_p
            messages = []

            if self.config.system_prompt:
                role = "developer" if self._is_reasoning_model else "system"
                messages.append({
                    "role": role,
                    "content": self.config.system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
            }

            # Reasoning models use max_completion_tokens; standard models use max_tokens
            if self._is_reasoning_model:
                request_params["max_completion_tokens"] = self.config.max_tokens
            else:
                request_params["max_tokens"] = self.config.max_tokens
                request_params["temperature"] = self.config.temperature

                # Add optional parameters (not supported by reasoning models)
                if self.config.top_p < 1.0:
                    request_params["top_p"] = self.config.top_p

                if self.config.stop_sequences:
                    request_params["stop"] = self.config.stop_sequences

            # Make the API call
            response = self.client.chat.completions.create(**request_params)

            # Extract response
            latency_ms = (time.time() - start_time) * 1000
            full_response = response.choices[0].message.content or ""

            # Parse answer and reasoning
            answer, reasoning = self.parse_response(full_response)

            # Get token usage
            tokens_used = 0
            if response.usage:
                tokens_used = response.usage.total_tokens

            return ModelResponse(
                answer=answer,
                reasoning=reasoning,
                full_response=full_response,
                model=self.model,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
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

    def generate_with_logprobs(self, prompt: str) -> ModelResponse:
        """
        Generate a response with log probabilities for confidence estimation.

        Args:
            prompt: The input prompt

        Returns:
            ModelResponse with confidence score
        """
        start_time = time.time()

        try:
            messages = []

            if self.config.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.config.system_prompt
                })

            messages.append({
                "role": "user",
                "content": prompt
            })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                logprobs=True,
                top_logprobs=5,
            )

            latency_ms = (time.time() - start_time) * 1000
            full_response = response.choices[0].message.content or ""

            # Parse response
            answer, reasoning = self.parse_response(full_response)

            # Calculate confidence from logprobs
            confidence = None
            if response.choices[0].logprobs:
                logprobs = response.choices[0].logprobs.content
                if logprobs:
                    # Average probability of first few tokens
                    import math
                    probs = [math.exp(lp.logprob) for lp in logprobs[:10] if lp.logprob]
                    if probs:
                        confidence = sum(probs) / len(probs)

            tokens_used = response.usage.total_tokens if response.usage else 0

            return ModelResponse(
                answer=answer,
                reasoning=reasoning,
                full_response=full_response,
                model=self.model,
                latency_ms=latency_ms,
                tokens_used=tokens_used,
                confidence=confidence,
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


def create_openai_runner(
    model: str = "gpt-4.1",
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> OpenAIRunner:
    """
    Create an OpenAI runner with common defaults.

    Args:
        model: Model name (gpt-4.1, o3, o4-mini, gpt-4o, etc.)
        api_key: Optional API key (defaults to OPENAI_API_KEY env var)
        temperature: Sampling temperature (ignored for o-series reasoning models)
        max_tokens: Maximum tokens to generate

    Returns:
        Configured OpenAIRunner
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
    return OpenAIRunner(config)
