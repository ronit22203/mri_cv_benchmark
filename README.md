# mri-vision-benchmark

An empirical benchmarking harness comparing local open-source vision architectures against OpenAI frontier models on medical MRI diagnostic tasks—evaluating **accuracy**, **latency**, and **inference economics**.

---

## Overview

As local-first AI and edge deployment become critical for healthcare infrastructure, determining the performance trade-offs of running open-source vision models versus closed frontier models is paramount. This repository provides a deterministic, reproducible evaluation pipeline to benchmark models on MRI image interpretation, quantifying exact cost, speed, and diagnostic fidelity.

---

## Key Features

* **Dual-Architecture Evaluation:** Test local models (e.g., Llama-3.2-Vision, Qwen2-VL) side-by-side with frontier APIs (e.g., GPT-4o).
* **Comprehensive Telemetry:** Track granular metrics across inference runs:
* **Accuracy:** Diagnostic correctness against ground-truth clinical annotations.
* **Latency:** Time-to-first-token (TTFT), total generation time, and throughput (tokens/sec).
* **Inference Economics:** Cost per 1,000 inferences and token utilization efficiency.


* **Reproducible Harness:** Modular Python evaluation scripts designed for easy extension to custom datasets and model endpoints.

---

## Repository Structure

```text
mri-vision-benchmark/
├── assets/                  # Architecture diagrams and benchmark plots
├── data/                    # Sample evaluation datasets and ground-truth schemas
├── notebooks/               # Reproducible Jupyter notebooks for exploratory analysis
├── src/
│   ├── evaluators/          # Core benchmarking logic and metric calculators
│   ├── models/              # Wrappers for local (vLLM/Ollama) and API clients
│   └── utils/               # Logging, telemetry, and data parsers
├── .env.example             # Template for API keys and local endpoints
├── requirements.txt         # Project dependencies
└── README.md

```

---

## Quick Start

### 1. Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/your-username/mri-vision-benchmark.git
cd mri-vision-benchmark
pip install -r requirements.txt

```

### 2. Configuration

Copy the environment template and configure your API keys and local inference endpoints:

```bash
cp .env.example .env

```

Edit `.env` to add your OpenAI API key and local model server URLs (if utilizing vLLM/Ollama).

### 3. Running a Benchmark

Execute the evaluation script against the sample dataset:

```bash
python -m src.evaluators.run_benchmark --config configs/default_eval.yaml

```

---

## Roadmap

* [ ] Implement core evaluation harness for accuracy and latency metrics.
* [ ] Add cost tracking wrapper for API-based frontier models.
* [ ] Publish interactive Jupyter notebook (`notebooks/analysis.ipynb`) for deep-dive exploratory data analysis.
* [ ] Expand model matrix to include fine-tuned domain-specific open-source checkpoints.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
