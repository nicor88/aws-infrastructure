# provider
provider "aws" {
  region = "us-east-1"
}

# modules
module "ec2" {
  source = "./ec2"
}
