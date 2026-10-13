terraform {
  required_version = ">= 1.5.0"

  required_providers {
    runpod = {
      source  = "decentralized-infrastructure/runpod"
      version = "~> 1.0"
    }
  }
}

provider "runpod" {
  # Reads RUNPOD_API_KEY from the environment.
}
