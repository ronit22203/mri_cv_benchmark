resource "runpod_pod" "inference_worker" {
  name                 = "medical-cv-vllm-node"
  image_name           = var.container_image
  gpu_type_ids         = [var.gpu_type_id]
  gpu_count            = 1
  cloud_type           = var.cloud_type
  container_disk_in_gb = 50
  volume_in_gb         = var.volume_size_gb
  volume_mount_path    = "/root/.cache/huggingface"
  support_public_ip    = true

  ports = ["8000/http", "22/tcp"]

  # Image ENTRYPOINT is already `vllm serve`. The model name is the first argument.
  # A 24 GB GPU only has a few hundred MB left after the weights load, so the
  # context has to stay short. Classification does not need the 32k default.
  docker_start_cmd = [
    var.model_name,
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--trust-remote-code",
    "--max-model-len",
    "4096",
    "--gpu-memory-utilization",
    "0.95",
  ]
}

output "pod_id" {
  value = runpod_pod.inference_worker.id
}

output "public_ip" {
  value = runpod_pod.inference_worker.public_ip
}

output "openai_base_url" {
  value = "http://${runpod_pod.inference_worker.public_ip}:8000/v1"
}
