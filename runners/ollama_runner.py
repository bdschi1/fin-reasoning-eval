"""
Ollama Runner for Financial Reasoning Eval Benchmark

Supports locally-running Ollama models via OpenAI-compatible API.
Ollama runs at http://localhost:11434 by default.
"""

import json
import os
import time
import urllib.error
import urllib.request
from typing import Optional

from .base import BaseRunner, RunnerConfig, ModelResponse

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def is_ollama_running(base_url: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running at the given URL."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def list_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """List available models from a running Ollama instance."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError):
        return []


class OllamaRunner(BaseRunner):
    """Runner for locally-hosted Ollama models via OpenAI-compatible API."""

    # Common Ollama model aliases for convenience
    MODEL_ALIASES = {
        "llama3.2": "llama3.2:latest",
        "llama3.1": "llama3.1:latest",
        "llama3": "llama3:latest",
        "mistral": "mistral:latest",
        "mixtral": "mixtral:latest",
        "phi3": "phi3:latest",
        "phi4": "phi4:latest",
        "qwen2.5": "qwen2.5:latest",
        "deepseek-r1": "deepseek-r1:latest",
        "gemma2": "gemma2:latest",
        "codellama": "codellama:latest",
    }

    def __init__(self, config: RunnerConfig):
        """
        Initialize the Ollama runner.

        Args:
            config: Runner configuration
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            )

        super().__init__(config)

        # Ollama base URL (OLLAMA_HOST is Ollama's own standard env var)
        self.base_url = config.api_base or os.environ.get(
            "OLLAMA_HOST", "http://localhost:11434"
        )

        # Verify Ollama is running
        if not is_ollama_running(self.base_url):
            raise ConnectionError(
                f"Ollama is not running at {self.base_url}. "
                "Start Ollama with: ollama serve"
            )

        # Initialize OpenAI client pointed at Ollama's compatible endpoint
        self.client = openai.OpenAI(
            api_key="ollama",  # Ollama ignores this but the client requires it
            base_url=f"{self.base_url}/v1",
        )

        # Resolve model alias
        self.model = self.MODEL_ALIASES.get(
            config.model_name.lower(),
            config.model_name,
        )

    def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response using Ollama's OpenAI-compatible API.

        Args:
            prompt: The input prompt

        Returns:
            ModelResponse with the model's output
        """
        start_time = time.time()

        try:
            # Build messages
            messages = []

            if self.config.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.config.system_prompt,
                })

            messages.append({
                "role": "user",
                "content": prompt,
            })

            # Build request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }

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


def create_ollama_runner(
    model: str = "llama3.2",
    base_url: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> OllamaRunner:
    """
    Create an Ollama runner with common defaults.

    Args:
        model: Model name (as known to Ollama, e.g., llama3.2, mistral, phi3)
        base_url: Ollama API base URL (default: http://localhost:11434)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        Configured OllamaRunner
    """
    config = RunnerConfig(
        model_name=model,
        api_base=base_url,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=(
            "You are a financial analyst with expertise in evaluating financial models, "
            "analyzing earnings, and assessing investment opportunities. "
            "Provide clear, well-reasoned answers to financial questions. "
            "Always show your reasoning step by step before providing your final answer."
        ),
    )
    return OllamaRunner(config)
