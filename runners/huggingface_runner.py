"""
HuggingFace Runner for Financial Reasoning Eval Benchmark

Supports local models and HuggingFace Inference API:
- Llama 3.1 8B/70B
- Mistral
- Other transformers models
"""

import os
import time
from typing import Optional, Union

from .base import BaseRunner, RunnerConfig, ModelResponse

# Try importing transformers for local inference
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    torch = None

# Try importing huggingface_hub for API inference
try:
    from huggingface_hub import InferenceClient
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False


class HuggingFaceRunner(BaseRunner):
    """
    Runner for HuggingFace models.

    Supports both local inference and HuggingFace Inference API.
    """

    # Common model IDs
    MODEL_IDS = {
        # Llama (current)
        "llama-4-scout": "meta-llama/Llama-4-Scout-17B-16E-Instruct",
        "llama-4-maverick": "meta-llama/Llama-4-Maverick-17B-128E-Instruct",
        "llama-3.3-70b": "meta-llama/Llama-3.3-70B-Instruct",
        # Llama (previous)
        "llama-3.1-8b": "meta-llama/Llama-3.1-8B-Instruct",
        "llama-3.1-70b": "meta-llama/Llama-3.1-70B-Instruct",
        "llama-3.1-405b": "meta-llama/Llama-3.1-405B-Instruct",
        # Mistral
        "mistral-small": "mistralai/Mistral-Small-24B-Instruct-2501",
        "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        # Qwen
        "qwen2.5-72b": "Qwen/Qwen2.5-72B-Instruct",
        "qwen2.5-7b": "Qwen/Qwen2.5-7B-Instruct",
        # DeepSeek
        "deepseek-r1": "deepseek-ai/DeepSeek-R1",
        "deepseek-v3": "deepseek-ai/DeepSeek-V3",
        # Legacy
        "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.3",
        "phi-3-mini": "microsoft/Phi-3-mini-4k-instruct",
        "qwen2-7b": "Qwen/Qwen2-7B-Instruct",
    }

    def __init__(
        self,
        config: RunnerConfig,
        use_api: bool = True,
        device: Optional[str] = None,
        torch_dtype: Optional[str] = None,
        load_in_8bit: bool = False,
        load_in_4bit: bool = False,
    ):
        """
        Initialize the HuggingFace runner.

        Args:
            config: Runner configuration
            use_api: Use HuggingFace Inference API (default) or local inference
            device: Device for local inference ('cuda', 'cpu', 'mps')
            torch_dtype: Torch dtype for local inference ('float16', 'bfloat16')
            load_in_8bit: Load model in 8-bit precision
            load_in_4bit: Load model in 4-bit precision
        """
        super().__init__(config)

        self.use_api = use_api
        self.model_id = self.MODEL_IDS.get(
            config.model_name.lower(),
            config.model_name
        )

        if use_api:
            self._init_api_client()
        else:
            self._init_local_model(device, torch_dtype, load_in_8bit, load_in_4bit)

    def _init_api_client(self):
        """Initialize HuggingFace Inference API client."""
        if not HF_HUB_AVAILABLE:
            raise ImportError(
                "huggingface_hub not installed. Install with: pip install huggingface_hub"
            )

        api_key = self.config.api_key or os.environ.get("HF_API_KEY")
        self.client = InferenceClient(
            model=self.model_id,
            token=api_key,
            timeout=self.config.timeout,
        )

    def _init_local_model(
        self,
        device: Optional[str],
        torch_dtype: Optional[str],
        load_in_8bit: bool,
        load_in_4bit: bool,
    ):
        """Initialize local model for inference."""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers not installed. Install with: pip install transformers torch"
            )

        # Determine device
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"

        self.device = device

        # Determine dtype
        dtype_map = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        dtype = dtype_map.get(torch_dtype, torch.float16 if device == "cuda" else torch.float32)

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": dtype,
        }

        if load_in_8bit:
            model_kwargs["load_in_8bit"] = True
            model_kwargs["device_map"] = "auto"
        elif load_in_4bit:
            model_kwargs["load_in_4bit"] = True
            model_kwargs["device_map"] = "auto"
        elif device != "cpu":
            model_kwargs["device_map"] = "auto"

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            **model_kwargs,
        )

        # Create pipeline for easier inference
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device_map="auto" if device != "cpu" else None,
        )

    def generate(self, prompt: str) -> ModelResponse:
        """
        Generate a response.

        Args:
            prompt: The input prompt

        Returns:
            ModelResponse with the model's output
        """
        if self.use_api:
            return self._generate_api(prompt)
        else:
            return self._generate_local(prompt)

    def _generate_api(self, prompt: str) -> ModelResponse:
        """Generate using HuggingFace Inference API."""
        start_time = time.time()

        try:
            # Format prompt for chat models
            formatted_prompt = self._format_chat_prompt(prompt)

            # Make API call
            response = self.client.text_generation(
                formatted_prompt,
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature if self.config.temperature > 0 else None,
                top_p=self.config.top_p if self.config.top_p < 1.0 else None,
                stop_sequences=self.config.stop_sequences or None,
                return_full_text=False,
            )

            latency_ms = (time.time() - start_time) * 1000
            full_response = response

            # Parse answer and reasoning
            answer, reasoning = self.parse_response(full_response)

            return ModelResponse(
                answer=answer,
                reasoning=reasoning,
                full_response=full_response,
                model=self.model_id,
                latency_ms=latency_ms,
                success=True,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ModelResponse(
                answer="",
                full_response="",
                model=self.model_id,
                latency_ms=latency_ms,
                error=str(e),
                success=False,
            )

    def _generate_local(self, prompt: str) -> ModelResponse:
        """Generate using local model."""
        start_time = time.time()

        try:
            # Format prompt for chat models
            formatted_prompt = self._format_chat_prompt(prompt)

            # Generate
            outputs = self.pipe(
                formatted_prompt,
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature if self.config.temperature > 0 else None,
                top_p=self.config.top_p if self.config.top_p < 1.0 else None,
                do_sample=self.config.temperature > 0,
                pad_token_id=self.tokenizer.pad_token_id,
                return_full_text=False,
            )

            latency_ms = (time.time() - start_time) * 1000
            full_response = outputs[0]["generated_text"]

            # Parse answer and reasoning
            answer, reasoning = self.parse_response(full_response)

            return ModelResponse(
                answer=answer,
                reasoning=reasoning,
                full_response=full_response,
                model=self.model_id,
                latency_ms=latency_ms,
                success=True,
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ModelResponse(
                answer="",
                full_response="",
                model=self.model_id,
                latency_ms=latency_ms,
                error=str(e),
                success=False,
            )

    def _format_chat_prompt(self, prompt: str) -> str:
        """Format prompt for chat models using the tokenizer's chat template."""
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

        # Use tokenizer's chat template if available
        if hasattr(self, 'tokenizer') and hasattr(self.tokenizer, 'apply_chat_template'):
            return self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

        # Fallback for API usage
        return self._format_llama_style(messages)

    def _format_llama_style(self, messages: list[dict]) -> str:
        """Format messages in Llama-style chat format."""
        formatted = ""

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                formatted += f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "user":
                formatted += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "assistant":
                formatted += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"

        formatted += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return formatted


def create_llama_runner(
    model_size: str = "8b",
    use_api: bool = True,
    api_key: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> HuggingFaceRunner:
    """
    Create a Llama 3.1 runner.

    Args:
        model_size: Model size ('8b' or '70b')
        use_api: Use HuggingFace Inference API
        api_key: Optional HuggingFace API key
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        Configured HuggingFaceRunner
    """
    model_name = f"llama-3.1-{model_size}"

    config = RunnerConfig(
        model_name=model_name,
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

    return HuggingFaceRunner(config, use_api=use_api)
