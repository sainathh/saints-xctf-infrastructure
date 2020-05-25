/**
 * Set up an API Gateway service for lambda functions.
 * Author: Andrew Jarombek
 * Date: 5/24/2020
 */

locals {
  env = var.prod ? "prodution" : "development"
}

#-----------------------
# Existing AWS Resources
#-----------------------

data "template_file" "api-gateway-auth-policy-file" {
  template = file("${path.module}/api-gateway-auth-policy.json")

  vars = {
    lambda_arn = var.auth-lambda-invoke-arn
  }
}

#----------------------------------
# New AWS Resources for API Gateway
#----------------------------------

resource "aws_api_gateway_rest_api" "saints-xctf-com-api" {
  name = "saints-xctf-com-api"
  description = "A REST API for AWS Lambda Functions used with saintsxctf.com"
}

resource "aws_api_gateway_authorizer" "saints-xctf-com-api-authorizer" {
  type = "TOKEN"
  name = "saints-xctf-com-api-auth"
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  authorizer_uri = var.auth-lambda-invoke-arn
}

resource "aws_iam_role" "auth-invocation-role" {
  name = "api-gateway-auth-role"
  path = "/saints-xctf-com/"
  assume_role_policy = file("${path.module}/api-gateway-auth-role.json")
  description = "IAM Role for invoking an authentication Lambda function from API Gateway"
}

resource "aws_iam_policy" "auth-invocation-policy" {
  name = "api-gateway-auth-policy"
  path = "/saints-xctf-com/"
  policy = data.template_file.api-gateway-auth-policy-file.rendered
  description = "IAM Policy for invoking an authentication Lambda function from API Gateway"
}

resource "aws_iam_role_policy_attachment" "auth-invocation-role-policy-attachment" {
  policy_arn = aws_iam_policy.auth-invocation-policy.arn
  role = aws_iam_role.auth-invocation-role.name
}

# API Endpoints
# -------------
# /email/welcome
# /email/forgot-password

# Resource for the API path /email
resource "aws_api_gateway_resource" "saints-xctf-com-api-email-path" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  parent_id = aws_api_gateway_rest_api.saints-xctf-com-api.root_resource_id
  path_part = "email"
}

# Resource for the API path /email/welcome
resource "aws_api_gateway_resource" "saints-xctf-com-api-welcome-path" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  parent_id = aws_api_gateway_resource.saints-xctf-com-api-email-path.id
  path_part = "welcome"
}

# Resource for the API path /email/forgot-password
resource "aws_api_gateway_resource" "saints-xctf-com-api-forgot-password-path" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  parent_id = aws_api_gateway_resource.saints-xctf-com-api-email-path.id
  path_part = "forgot-password"
}

resource "aws_api_gateway_method" "email-forgot-password-method" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  resource_id = aws_api_gateway_resource.saints-xctf-com-api-forgot-password-path.id
  request_validator_id = aws_api_gateway_request_validator.email-forgot-password-request-validator.id

  http_method = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_request_validator" "email-forgot-password-request-validator" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  validate_request_body = true
  name = "email-forgot-password-request-body"
}

resource "aws_api_gateway_method_response" "email-forgot-password-method-response" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  resource_id = aws_api_gateway_resource.saints-xctf-com-api-forgot-password-path.id

  http_method = aws_api_gateway_method.email-forgot-password-method.http_method
  status_code = "200"
}

resource "aws_api_gateway_integration" "email-forgot-password-integration" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  resource_id = aws_api_gateway_resource.saints-xctf-com-api-forgot-password-path.id

  http_method = aws_api_gateway_method.email-forgot-password-method.http_method

  # Lambda functions can only be invoked via HTTP POST
  integration_http_method = "POST"

  type = "AWS"
  uri = var.email-lambda-invoke-arn

  request_templates = {
    "application/json" = file("${path.module}/request.vm")
  }
}

resource "aws_api_gateway_integration_response" "email-forgot-password-integration-response" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  resource_id = aws_api_gateway_resource.saints-xctf-com-api-forgot-password-path.id

  http_method = aws_api_gateway_method.email-forgot-password-method.http_method
  status_code = aws_api_gateway_method_response.email-forgot-password-method-response.status_code

  response_templates = {
    "application/json" = file("${path.module}/response.vm")
  }

  depends_on = [
    aws_api_gateway_integration.email-forgot-password-integration
  ]
}

resource "aws_lambda_permission" "allow_api_gateway" {
  action = "lambda:InvokeFunction"
  function_name = var.email-lambda-name
  statement_id = "AllowExecutionFromApiGateway"
  principal = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.saints-xctf-com-api.execution_arn}/*/*/*"
}

resource "aws_api_gateway_deployment" "saints-xctf-com-api-deployment" {
  rest_api_id = aws_api_gateway_rest_api.saints-xctf-com-api.id
  stage_name = local.env

  depends_on = [
    aws_api_gateway_integration.email-forgot-password-integration,
    aws_api_gateway_integration_response.email-forgot-password-integration-response
  ]
}