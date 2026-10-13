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

variable "data_center_id" {
  type        = string
  description = "RunPod data center for the network volume and the pod. The volume and pod must share a region."
  default     = "US-CA-2"
}

variable "container_image" {
  type    = string
  default = "vllm/vllm-openai:latest"
}

variable "model_name" {
  type        = string
  description = "Hugging Face model served by vLLM."
  default     = "Qwen/Qwen2-VL-7B-Instruct"
}

variable "volume_size_gb" {
  type    = number
  default = 50
}
