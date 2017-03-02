import os
import boto3

session = boto3.Session(profile_name='nicor88-aws-dev')
s3_client = session.client('s3')


# TODO create a security group
# TODO create an EC2 machine

