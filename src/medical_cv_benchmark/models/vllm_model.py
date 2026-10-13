import time
from typing import Any

from openai import OpenAI
from PIL import Image

from medical_cv_benchmark.models.base import BaseModelAdapter, encode_image_jpeg


class VLLMModelAdapter(BaseModelAdapter):
    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        model_name: str = "Qwen/Qwen2-VL-7B-Instruct",
        max_tokens: int = 300,
        temperature: float = 0.0,
    ):
        # vLLM exposes an OpenAI-compatible server and ignores the API key.
        self.client = OpenAI(base_url=base_url, api_key="EMPTY")
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature

    def evaluate_image(self, image: Image.Image, prompt: str) -> dict[str, Any]:
        base64_image = encode_image_jpeg(image)

        start_time = time.perf_counter()
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
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
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
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
