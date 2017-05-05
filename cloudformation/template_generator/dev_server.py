import boto3

session = boto3.Session(profile_name='nicor88-aws-dev')
cfn = session.client('cloudformation')

from troposphere import FindInMap, Parameter, Ref, Tags, Template

# TODO create a security group
# TODO create an EC2 machine
# Deploy using code deploy
# cfn-hup setup

STACK_NAME = 'DevServer'

template = Template()
description = 'Dev Server Stack Free Tier'
template.add_description(description)