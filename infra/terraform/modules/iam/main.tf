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

# Allow GitHub Actions to access Terraform state in S3
resource "aws_iam_role_policy" "terraform_state" {
  name = "dataforge-terraform-state-access"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]

        Resource = "${var.bucket_arn}/terraform/state/dev/*"
      },
      {
        Effect = "Allow"

        Action = [
          "s3:ListBucket"
        ]

        Resource = var.bucket_arn

        Condition = {
          StringLike = {
            "s3:prefix" = [
              "terraform/state/dev/*"
            ]
          }
        }
      }
    ]
  })
}