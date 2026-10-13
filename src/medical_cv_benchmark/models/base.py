import base64
import io
from abc import ABC, abstractmethod
from typing import Any

from PIL import Image


def encode_image_jpeg(image: Image.Image) -> str:
    """Encode an image as a base64 JPEG. RGB conversion covers grayscale MRI slices."""
    frame = image.convert("RGB")
    buffer = io.BytesIO()
    frame.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class BaseModelAdapter(ABC):
    @abstractmethod
    def evaluate_image(self, image: Image.Image, prompt: str) -> dict[str, Any]:
        """Run one image through the model and return the prediction plus usage metrics."""
