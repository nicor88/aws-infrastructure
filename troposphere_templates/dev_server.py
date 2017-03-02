import boto3

session = boto3.Session(profile_name='nicor88-aws-dev')
cfn = session.client('cloudformation')

# TODO create a security group
# TODO create an EC2 machine

STACK_NAME = 'DevServer'
