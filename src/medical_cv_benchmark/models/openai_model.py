import time
from typing import Any

from openai import OpenAI
from PIL import Image

from medical_cv_benchmark.models.base import BaseModelAdapter, encode_image_jpeg

GPT_6_ASTRA = "gpt-6-astra"
GPT_6_1_SOL = "gpt-6.1-sol"
GPT_6_LUNA = "gpt-6-luna"


def default_reasoning_effort(model_name: str) -> str | None:
    """Cheapest effort each GPT-6 tier accepts. Older models do not use this parameter."""
    key = model_name.lower()
    if not key.startswith("gpt-6"):
        return None
    # Luna accepts effort "none". Astra and Sol reject it and start at "low".
    if key == GPT_6_LUNA or key.startswith(f"{GPT_6_LUNA}-"):
        return "none"
    return "low"


class OpenAIModelAdapter(BaseModelAdapter):
    def __init__(
        self,
        model_name: str = GPT_6_1_SOL,
        api_key: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        reasoning_effort: str | None = None,
    ):
        client_kwargs: dict[str, str] = {}
        if api_key is not None:
            client_kwargs["api_key"] = api_key
        self.client = OpenAI(**client_kwargs)
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        if reasoning_effort is None:
            reasoning_effort = default_reasoning_effort(model_name)
        self.reasoning_effort = reasoning_effort

    def evaluate_image(self, image: Image.Image, prompt: str) -> dict[str, Any]:
        base64_image = encode_image_jpeg(image)
        request: dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        }
        # Reasoning tokens count against the completion cap. Temperature is
        # rejected unless effort is omitted or explicitly "none".
        if self.reasoning_effort is None:
            request["max_tokens"] = self.max_tokens
            request["temperature"] = self.temperature
        else:
            request["reasoning_effort"] = self.reasoning_effort
            request["max_completion_tokens"] = self.max_tokens
            if self.reasoning_effort == "none":
                request["temperature"] = self.temperature

        start_time = time.perf_counter()
        response = self.client.chat.completions.create(**request)
        latency = time.perf_counter() - start_time

        content = response.choices[0].message.content or ""
        usage = response.usage

        return {
            "model": self.model_name,
            "prediction": content,
            "latency_seconds": latency,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }
