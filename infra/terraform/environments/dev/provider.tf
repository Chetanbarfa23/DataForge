terraform {
  required_version = ">= 1.10.0"

  backend "s3" {
    bucket       = "dataforge-bronze-chetan-2026"
    key          = "terraform/state/dev/terraform.tfstate"
    region       = "ap-southeast-2"
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}