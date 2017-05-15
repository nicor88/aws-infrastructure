import os
import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import ec2
from troposphere import Template, Tags, Output, Ref, Parameter

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'dev_config.yml'))

# setup aws session
os.environ['AWS_DEFAULT_REGION'] = cfg['region']
os.environ['AWS_PROFILE'] = 'nicor88-aws-dev'
cfn = boto3.client('cloudformation')


STACK_NAME = cfg['ec2']['stack_name']

template = Template()
description = 'Dev Server Stack Free Tier'
template.add_description(description)
# AWSTemplateFormatVersion
template.add_version('2010-09-09')

# security group

ssh = template.add_resource(
    ec2.SecurityGroup(
        'SSH',
        VpcId=cfg['network']['vpc_id'],
        GroupDescription='Allow SSH traffic',
        SecurityGroupIngress=[
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='22',
                ToPort='22',
                CidrIp='0.0.0.0/0'
            )
        ],
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            Name='all-ssh'
        )
    )
)

# ec2 instance
ec2_instance = template.add_resource(ec2.Instance(
    'DevServer',
    InstanceType=cfg['ec2']['instance_type'],
    ImageId=cfg['ec2']['ami_version'],
    SecurityGroupIds=[Ref('SSH')],
    InstanceInitiatedShutdownBehavior='stop',
    Tags=Tags(
        StackName=Ref('AWS::StackName'),
        Name='dev-server',
        )
    )
)

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'DevServer'
        }
    ]
}

cfn.validate_template(TemplateBody=template_json)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
