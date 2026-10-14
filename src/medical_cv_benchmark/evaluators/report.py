from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from medical_cv_benchmark.evaluators.runner import summarize

_METRIC_COLUMNS = (
    "image_path",
    "model",
    "ground_truth",
    "predicted_label",
    "correct",
    "latency_seconds",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "cost_usd",
    "error",
)

_SUMMARY_COLUMNS = (
    "model",
    "n",
    "accuracy",
    "mean_latency_seconds",
    "cost_per_1000_usd",
)


def benchmarks_dir() -> Path:
    """Project-level benchmarks/ directory, independent of the working directory."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent / "benchmarks"
    return Path.cwd() / "benchmarks"


def write_benchmark_report(results: pd.DataFrame, output_dir: Path | None = None) -> Path:
    """Write summary and per-image metrics to a new markdown file."""
    directory = output_dir or benchmarks_dir()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    path = directory / f"{stamp}.md"
    path.write_text(render_benchmark_markdown(results), encoding="utf-8")
    return path


def render_benchmark_markdown(results: pd.DataFrame) -> str:
    written_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = summarize(results)
    sections = [
        "# MRI benchmark",
        "",
        f"Written: {written_at}",
        "",
        "## Summary",
        "",
        _markdown_table(summary, _SUMMARY_COLUMNS, _format_summary_cell),
        "",
        "## Per-image metrics",
        "",
        _markdown_table(results, _METRIC_COLUMNS, _format_metric_cell),
        "",
        "## Predictions",
        "",
        _prediction_sections(results),
        "",
    ]
    return "\n".join(sections)


def _markdown_table(
    frame: pd.DataFrame,
    columns: tuple[str, ...],
    format_cell,
) -> str:
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    if frame.empty:
        return "\n".join([header, divider, "| " + " | ".join("" for _ in columns) + " |"])

    lines = [header, divider]
    for _, row in frame.iterrows():
        cells = [_escape_cell(format_cell(column, row.get(column))) for column in columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _format_summary_cell(column: str, value: Any) -> str:
    if _missing(value):
        return ""
    if column == "accuracy":
        return f"{float(value):.3f}"
    if column == "mean_latency_seconds":
        return f"{float(value):.3f}"
    if column == "cost_per_1000_usd":
        return f"{float(value):.6f}"
    if column == "n":
        return str(int(value))
    return str(value)


def _format_metric_cell(column: str, value: Any) -> str:
    if _missing(value):
        return ""
    if column == "latency_seconds":
        return f"{float(value):.3f}"
    if column == "cost_usd":
        return f"{float(value):.6f}"
    if column in {"prompt_tokens", "completion_tokens", "total_tokens"}:
        return str(int(value))
    if column == "correct":
        return "yes" if bool(value) else "no"
    if column == "image_path":
        return Path(str(value)).name
    return str(value)


def _prediction_sections(results: pd.DataFrame) -> str:
    if results.empty or "prediction" not in results.columns:
        return "_No predictions._"

    blocks: list[str] = []
    for index, row in results.iterrows():
        image = Path(str(row.get("image_path") or "")).name or f"row-{index}"
        model = row.get("model") or "model"
        prediction = "" if _missing(row.get("prediction")) else str(row.get("prediction"))
        fence = "````" if "```" in prediction else "```"
        blocks.append(
            "\n".join(
                [
                    f"### {image} — {model}",
                    "",
                    f"- Ground truth: {row.get('ground_truth')}",
                    f"- Predicted: {row.get('predicted_label') or ''}",
                    f"- Correct: {_format_metric_cell('correct', row.get('correct'))}",
                    "",
                    fence,
                    prediction,
                    fence,
                    "",
                ]
            )
        )
    return "\n".join(blocks).rstrip()


def _missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return False
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _escape_cell(value: str) -> str:
    return value.replace("\n", " ").replace("|", "\\|")
