# Persistent storage so model weights survive pod replacement.
resource "runpod_network_volume" "model_cache" {
  name           = "vllm-model-cache"
  size           = var.volume_size_gb
  data_center_id = var.data_center_id
}

resource "runpod_pod" "inference_worker" {
  name                 = "medical-cv-vllm-node"
  image_name           = var.container_image
  gpu_type_ids         = [var.gpu_type_id]
  gpu_count            = 1
  cloud_type           = var.cloud_type
  data_center_ids      = [var.data_center_id]
  container_disk_in_gb = 50
  volume_in_gb         = var.volume_size_gb
  volume_mount_path    = "/root/.cache/huggingface"
  network_volume_id    = runpod_network_volume.model_cache.id
  support_public_ip    = true

  ports = ["8000/http", "22/tcp"]

  # Image ENTRYPOINT is `vllm`. `serve` plus the model name is the start command.
  docker_start_cmd = [
    "serve",
    var.model_name,
    "--host",
    "0.0.0.0",
    "--port",
    "8000",
    "--trust-remote-code",
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
