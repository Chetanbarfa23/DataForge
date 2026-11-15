output "bucket_name" {
    description = "Existing S3 bucket name"
    value       = data.aws_s3_bucket.this.id
}

output "bucket_region" {
    description = "Existing S3 bucket region"
    value       = data.aws_s3_bucket.this.region
}
