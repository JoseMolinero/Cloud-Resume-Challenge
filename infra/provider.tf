terraform {
    required_version = ">= 1.5.0"
    required_providers {
        aws = {
            version = ">= 5.0, < 7.0"
            source = "hashicorp/aws"
        }
        archive = {
            version = "~> 2.0"
            source = "hashicorp/archive"
        }
    }
}
provider "aws" {
    profile="default"
    region = "eu-west-2"
}
