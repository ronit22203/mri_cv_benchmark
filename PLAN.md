## What We Are Actually Building

We are treating closed-source frontier models and local open-source vision models as **"black box" diagnostic APIs**:

- **The Target Task:** Feed an MRI scan from the Kaggle dataset into a model alongside a structured prompt
  _e.g._, _"Analyze this brain MRI. Classify it into one of four categories: glioma, meningioma, pituitary, or no tumor. Provide your clinical reasoning."_

- **The Frontier Challenger:**
  GPT-4o (via the OpenAI API), using KAGGLE_API_TOKEN to evaluate a subset of test images.

- **The Local Challenger:**
  Open-source vision-language models like Qwen2-VL-7B or Llama-3.2-11B-Vision hosted on RunPod instance.

- **The Benchmark Outputs:**
  Models are compared on three axes:
  - **Accuracy:** Did the model pick the correct tumor class compared to the dataset ground truth?
  - **Latency:** Time-to-first-token and total inference time.
  - **Unit Economics:** Cost per 1,000 inferences ($0 for local RunPod vs. API costs for OpenAI).
