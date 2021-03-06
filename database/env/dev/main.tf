/**
 * Infrastructure for the saintsxctf database in the DEV environment
 * Author: Andrew Jarombek
 * Date: 12/5/2018
 */

provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = ">= 0.12"

  backend "s3" {
    bucket = "andrew-jarombek-terraform-state"
    encrypt = true
    key = "saints-xctf-infrastructure/database/env/dev"
    region = "us-east-1"
  }
}

module "rds" {
  source = "../../modules/rds"
  prod = false
  username = var.username
  password = var.password
}