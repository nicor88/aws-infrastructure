resource "aws_instance" "dev-server" {
    ami = "ami-a8d2d7ce"
    instance_type = "t2.micro"
    subnet_id = "${aws_subnet.dev-eu-west-1b.id}"
    tags {
        Name = "dev-server"
    }
}
