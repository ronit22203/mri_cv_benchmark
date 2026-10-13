import logging
from dataclasses import dataclass

logger = logging.getLogger("medical_cv_benchmark")


@dataclass(frozen=True)
class TokenPrice:
    input_per_million: float
    output_per_million: float


# Standard rates in USD per 1M tokens. Longer names win, so gpt-4o-mini is not
# billed as gpt-4o and gpt-6.1-sol is not billed as another gpt-6 tier.
# GPT-6 completion tokens include reasoning tokens.
OPENAI_TOKEN_PRICES: dict[str, TokenPrice] = {
    "gpt-6-astra": TokenPrice(input_per_million=10.00, output_per_million=50.00),
    "gpt-6.1-sol": TokenPrice(input_per_million=2.00, output_per_million=10.00),
    "gpt-6-luna": TokenPrice(input_per_million=0.10, output_per_million=0.50),
    "gpt-4o-mini": TokenPrice(input_per_million=0.15, output_per_million=0.60),
    "gpt-4o": TokenPrice(input_per_million=2.50, output_per_million=10.00),
}


def configure_logging(level: int = logging.INFO) -> None:
    if logger.handlers:
        logger.setLevel(level)
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def lookup_token_price(model: str) -> TokenPrice | None:
    key = model.lower()
    for name in sorted(OPENAI_TOKEN_PRICES, key=len, reverse=True):
        if key == name or key.startswith(f"{name}-"):
            return OPENAI_TOKEN_PRICES[name]
    return None


def estimate_cost_usd(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_seconds: float,
    hourly_rate_usd: float = 0.0,
) -> float:
    """Token cost for priced APIs. Local models use GPU time at hourly_rate_usd."""
    price = lookup_token_price(model)
    if price is not None:
        return (
            prompt_tokens * price.input_per_million + completion_tokens * price.output_per_million
        ) / 1_000_000
    return hourly_rate_usd * latency_seconds / 3600


def cost_per_thousand(costs: list[float]) -> float:
    if not costs:
        return 0.0
    return sum(costs) / len(costs) * 1000


def log_inference(
    *,
    model: str,
    ground_truth: str,
    predicted_label: str | None,
    correct: bool,
    latency_seconds: float,
    total_tokens: int,
    cost_usd: float,
    error: str | None = None,
) -> None:
    if error:
        logger.error("model=%s label=%s error=%s", model, ground_truth, error)
        return
    logger.info(
        "model=%s label=%s predicted=%s correct=%s latency=%.3fs tokens=%d cost_usd=%.6f",
        model,
        ground_truth,
        predicted_label,
        correct,
        latency_seconds,
        total_tokens,
        cost_usd,
    )
