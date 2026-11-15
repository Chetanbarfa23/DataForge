module "s3" {
  source = "../../modules/s3"

  bucket_name = var.bucket_name
}

module "iam" {
  source = "../../modules/iam"

  role_name  = "dataforge-github-actions"
  bucket_arn = "arn:aws:s3:::dataforge-bronze-chetan-2026"
}





