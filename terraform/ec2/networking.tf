variable "vpc_id" {
   default = "vpc-8b708fec"
}

resource "aws_subnet" "dev-eu-west-1a" {
    vpc_id     = "${var.vpc_id}"
    cidr_block = "172.31.0.0/24"
    availability_zone = "eu-west-1a"
    tags {
        Name = "dev-eu-west-1a"
    }
}

resource "aws_subnet" "dev-eu-west-1b" {
    vpc_id     = "${var.vpc_id}"
    cidr_block = "172.31.64.0/24"
    availability_zone = "eu-west-1b"
    tags {
        Name = "dev-eu-west-1b"
    }
}

resource "aws_subnet" "dev-eu-west-1c" {
    vpc_id     = "${var.vpc_id}"
    cidr_block = "172.31.128.0/24"
    availability_zone = "eu-west-1c"
    tags {
        Name = "dev-eu-west-1c"
    }
}




