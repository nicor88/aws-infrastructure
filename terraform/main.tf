# provider
provider "aws" {
  region = "eu-west-1"
  profile = "nicor88-aws-dev"
}

# modules
module "dev" {
  source = "./dev"
}
