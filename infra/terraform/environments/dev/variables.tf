variable "project_name" {
  description = "Name of the DataForge project"
  type        = string
  default     = "dataforge"
}

variable "aws_region" {
  description = "AWS region for DataForge infrastructure"
  type        = string
  default     = "ap-southeast-2"
}

variable "bucket_name" {
  description = "Existing DataForge S3 bucket"
  type        = string
  default     = "dataforge-bronze-chetan-2026"
}







