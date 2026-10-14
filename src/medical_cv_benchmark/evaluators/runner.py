from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image

from medical_cv_benchmark.models.base import BaseModelAdapter
from medical_cv_benchmark.utils.telemetry import configure_logging, estimate_cost_usd, logger

DEFAULT_PROMPT = (
    "Analyze this brain MRI. Classify it into one of four categories: "
    "glioma, meningioma, pituitary, or no tumor. Provide your clinical reasoning. "
    "End with a line in the form: Classification: <label>."
)

# Longer aliases are matched first so "no tumor" wins over a bare token nearby.
_LABEL_ALIASES: tuple[tuple[str, str], ...] = (
    ("notumor", "notumor"),
    ("notumor", "no tumor"),
    ("notumor", "no-tumor"),
    ("notumor", "no_tumor"),
    ("meningioma", "meningioma"),
    ("pituitary", "pituitary"),
    ("glioma", "glioma"),
)


def parse_label(prediction: str) -> str | None:
    """Map a free-text answer onto glioma, meningioma, pituitary, or notumor."""
    text = prediction.lower()
    for line in reversed(text.splitlines()):
        if any(marker in line for marker in ("classification", "category", "diagnosis")):
            for label, alias in _LABEL_ALIASES:
                if alias in line:
                    return label

    last_at = -1
    found: str | None = None
    for label, alias in _LABEL_ALIASES:
        at = text.rfind(alias)
        if at > last_at:
            last_at = at
            found = label
    return found


def _list_images(class_dir: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in ("*.[jJ][pP][gG]", "*.[jJ][pP][eE][gG]", "*.[pP][nN][gG]"):
        paths.update(class_dir.glob(pattern))
    return sorted(paths)


def iter_labeled_images(
    dataset_path: Path,
    split: str = "Testing",
    limit_per_class: int | None = None,
):
    split_dir = Path(dataset_path) / split
    if not split_dir.is_dir():
        raise FileNotFoundError(f"Split directory not found: {split_dir}")

    class_dirs = sorted(path for path in split_dir.iterdir() if path.is_dir())
    for class_dir in class_dirs:
        images = _list_images(class_dir)
        if limit_per_class is not None:
            images = images[:limit_per_class]
        for image_path in images:
            yield class_dir.name, image_path


def _score_adapter(
    adapter: BaseModelAdapter,
    image: Image.Image,
    prompt: str,
    *,
    split: str,
    ground_truth: str,
    image_path: Path,
    hourly_rate_usd: float,
) -> dict[str, Any]:
    model_name = getattr(adapter, "model_name", adapter.__class__.__name__)
    row: dict[str, Any] = {
        "model": model_name,
        "split": split,
        "ground_truth": ground_truth,
        "image_path": str(image_path),
        "prediction": None,
        "predicted_label": None,
        "correct": False,
        "latency_seconds": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "error": None,
    }
    try:
        result = adapter.evaluate_image(image, prompt)
        predicted = parse_label(result["prediction"])
        cost = estimate_cost_usd(
            result["model"],
            result["prompt_tokens"],
            result["completion_tokens"],
            result["latency_seconds"],
            hourly_rate_usd=hourly_rate_usd,
        )
        row.update(
            {
                "model": result["model"],
                "prediction": result["prediction"],
                "predicted_label": predicted,
                "correct": predicted == ground_truth.lower(),
                "latency_seconds": result["latency_seconds"],
                "prompt_tokens": result["prompt_tokens"],
                "completion_tokens": result["completion_tokens"],
                "total_tokens": result["total_tokens"],
                "cost_usd": cost,
            }
        )
    except Exception as exc:
        row["error"] = str(exc)

    return row


def run_benchmark(
    adapters: list[BaseModelAdapter],
    dataset_path: Path,
    *,
    split: str = "Testing",
    limit_per_class: int | None = None,
    prompt: str = DEFAULT_PROMPT,
    hourly_rate_usd: float = 0.0,
    max_workers: int | None = None,
    output_dir: Path | None = None,
) -> pd.DataFrame:
    """Score each adapter on labeled MRI slices and return one row per inference.

    Adapters for the same image run concurrently. Latency is still measured
    inside each request, so overlap does not change the recorded timings.
    Metrics are written to a markdown file under benchmarks/.
    """
    from medical_cv_benchmark.evaluators.report import write_benchmark_report

    configure_logging()
    if not adapters:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    workers = max_workers or len(adapters)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for ground_truth, image_path in iter_labeled_images(dataset_path, split, limit_per_class):
            with Image.open(image_path) as image:
                frame = image.copy()
            futures = [
                pool.submit(
                    _score_adapter,
                    adapter,
                    frame.copy(),
                    prompt,
                    split=split,
                    ground_truth=ground_truth,
                    image_path=image_path,
                    hourly_rate_usd=hourly_rate_usd,
                )
                for adapter in adapters
            ]
            rows.extend(future.result() for future in futures)

    results = pd.DataFrame(rows)
    report_path = write_benchmark_report(results, output_dir)
    results.attrs["report_path"] = str(report_path)
    logger.info("benchmark report written to %s", report_path)
    return results


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    """Accuracy, mean latency, and cost per 1,000 successful inferences by model."""
    if results.empty:
        return pd.DataFrame(
            columns=["model", "n", "accuracy", "mean_latency_seconds", "cost_per_1000_usd"]
        )

    summaries: list[dict[str, Any]] = []
    for model, frame in results.groupby("model", dropna=False):
        scored = frame[frame["error"].isna()]
        n = len(scored)
        summaries.append(
            {
                "model": model,
                "n": n,
                "accuracy": float(scored["correct"].mean()) if n else float("nan"),
                "mean_latency_seconds": float(scored["latency_seconds"].mean()) if n else float("nan"),
                "cost_per_1000_usd": (
                    float(scored["cost_usd"].mean()) * 1000 if n else float("nan")
                ),
            }
        )
    return pd.DataFrame(summaries)
