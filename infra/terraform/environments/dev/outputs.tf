output "bucket_name" {
  description = "Existing DataForge S3 bucket name"
  value       = module.s3.bucket_name
}

output "bucket_region" {
  description = "Existing DataForge S3 bucket region"
  value       = module.s3.bucket_region
}

output "project_name" {
  description = "DataForge project name"
  value       = var.project_name
}
