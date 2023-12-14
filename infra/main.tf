resource "aws_lambda_function" "myfunc" {
    filename        = data.archive_file.zip.output_path
    source_code_hash= data.archive_file.zip.output_base64sha256
    function_name   = "myfunc"
    role            = aws_iam_role.iam_for_lambda.arn
    handler         = "func.lambda_handler"
    runtime         = "python3.8"
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
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource" : "arn:aws:logs:*:*:*",
                    "Effect" : "Allow"
                },
                {
                    "Effect" : "Allow",
                    "Action" : [
                        "dynamodb:UpdateItem",
                        "dynamodb:GetItem",
                        "dynamodb:PutItem"
                    ],
                    "Resource" : "arn:aws:dynamodb:*:*:table/visitas"
                },
            ]
        }
    )
}

resource "aws_iam_policy" "url_access" {
  name        = "url_access"
  path        = "/"
  description = "Permisos de acceso a url"

  policy = jsonencode(
    {
    "Version": "2012-10-17",
    "Id": "default",
    "Statement": [
        {
        "Sid": "FunctionURLAllowPublicAccess",
        "Effect": "Allow",
        "Action": "lambda:InvokeFunctionUrl",
        "Resource": "arn:aws:lambda:eu-west-2:445911943782:function:myfunc",
        "Condition": {
            "StringEquals": {
            "lambda:FunctionUrlAuthType": "NONE"
            }
        }
        }
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
        allow_credentials = true
        allow_origins   = ["*"]
        allow_methods   = ["*"]
        allow_headers   = ["date", "keep-alive"]
        expose_headers  = ["keep-alive", "date"]
        max_age         = 86400
    }
}