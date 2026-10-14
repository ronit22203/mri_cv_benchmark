variable "gpu_type_id" {
  type        = string
  description = "RunPod GPU type ID. Passed as a single-element gpu_type_ids list."
  default     = "NVIDIA GeForce RTX 4090"
}

variable "cloud_type" {
  type        = string
  description = "SECURE or COMMUNITY."
  default     = "SECURE"
}

variable "container_image" {
  type    = string
  default = "vllm/vllm-openai:latest"
}

variable "model_name" {
  type        = string
  description = "Hugging Face model served by vLLM."
  default     = "Qwen/Qwen3-VL-8B-Instruct"
}

variable "volume_size_gb" {
  type    = number
  default = 50
}
