variable "ip_retention_days" {
    type    = number
    default = 180

    validation {
        condition     = var.ip_retention_days >= 1 && var.ip_retention_days <= 365 && floor(var.ip_retention_days) == var.ip_retention_days
        error_message = "ip_retention_days must be a whole number between 1 and 365."
    }
}

variable "trust_cloudfront_headers" {
    type    = bool
    default = false
}

resource "aws_lambda_function" "myfunc" {
    filename        = data.archive_file.zip.output_path
    source_code_hash= data.archive_file.zip.output_base64sha256
    function_name   = "myfunc"
    role            = aws_iam_role.iam_for_lambda.arn
    handler         = "func.lambda_handler"
    runtime         = "python3.13"
    reserved_concurrent_executions = 2
    timeout         = 5

    environment {
        variables = {
            IP_RETENTION_DAYS = tostring(var.ip_retention_days)
            TRUST_CLOUDFRONT_HEADERS = tostring(var.trust_cloudfront_headers)
        }
    }
}

resource "aws_iam_role" "iam_for_lambda" {
    name = "iam_for_lambda"
    assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Effect": "Allow",
            "Sid": ""
        }
    ]
}
EOF
}

data "aws_caller_identity" "current" {}

resource "aws_iam_policy" "iam_policy_for_resume_proyect" {
  name = "aws_iam_policy_for_terraform_resume_proyect_policy"
  path = "/"
  description = "Politica IAM para el proyecto"
    policy = jsonencode(
        {
            "Version" : "2012-10-17",
            "Statement" : [
                {
                    "Action" : [
                        "logs:CreateLogGroup"
                    ],
                    "Resource" : "arn:aws:logs:eu-west-2:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/myfunc",
                    "Effect" : "Allow"
                },
                {
                    "Action" : [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource" : "arn:aws:logs:eu-west-2:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/myfunc:*",
                    "Effect" : "Allow"
                },
                {
                    "Effect" : "Allow",
                    "Action" : [
                        "dynamodb:UpdateItem"
                    ],
                    "Resource" : [
                        "arn:aws:dynamodb:eu-west-2:${data.aws_caller_identity.current.account_id}:table/visitas",
                        "arn:aws:dynamodb:eu-west-2:${data.aws_caller_identity.current.account_id}:table/direcciones"
                    ]
                },
            ]
        }
    )
}

resource "aws_iam_role_policy_attachment" "attach_iam_policy_to_iam_role" {
    role = aws_iam_role.iam_for_lambda.name
    policy_arn = aws_iam_policy.iam_policy_for_resume_proyect.arn
}

data "archive_file" "zip" {
    type        = "zip"
    source_dir  = "${path.module}/lambda/"
    output_path = "${path.module}/packedlambda.zip"
}

resource "aws_lambda_function_url" "url1" {
    function_name   = aws_lambda_function.myfunc.function_name
    authorization_type = "NONE"

    cors {
        allow_credentials = false
        allow_origins   = ["https://josemolinero.com", "https://www.josemolinero.com"]
        allow_methods   = ["POST"]
        max_age         = 86400
    }
}
