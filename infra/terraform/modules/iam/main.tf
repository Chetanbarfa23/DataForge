# Read existing GitHub OIDC provider
data "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
}

# GitHub Actions trust policy
data "aws_iam_policy_document" "github_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [data.aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:Chetanbarfa23@182407639/DataForge@1431878148:*"]
    }
  }
}

# Create GitHub Actions IAM role
resource "aws_iam_role" "github_actions" {
  name               = var.role_name
  assume_role_policy = data.aws_iam_policy_document.github_trust.json
}

# Permissions for GitHub Actions
resource "aws_iam_role_policy" "terraform_state" {
  name = "dataforge-terraform-state-access"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [

      # Access Terraform remote state
      {
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]

        Resource = "${var.bucket_arn}/terraform/state/dev/*"
      },

      # Inspect existing S3 bucket
      {
        Effect = "Allow"

        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]

        Resource = var.bucket_arn
      },

      # Inspect existing GitHub OIDC provider
      {
        Effect = "Allow"

        Action = [
          "iam:ListOpenIDConnectProviders"
        ]

        Resource = "*"
      },

      {
        Effect = "Allow"

        Action = [
          "iam:GetOpenIDConnectProvider"
        ]

        Resource = "arn:aws:iam::868335351942:oidc-provider/token.actions.githubusercontent.com"
      },

      # Read existing GitHub Actions IAM role and its policies
      {
        Effect = "Allow"

        Action = [
          "iam:GetRole",
          "iam:ListRolePolicies",
          "iam:GetRolePolicy",
          "iam:ListAttachedRolePolicies"
        ]

        Resource = "arn:aws:iam::868335351942:role/dataforge-github-actions"
      }
    ]
  })
}