import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import awslambda
from troposphere import Template, Tags, Output, Ref, Parameter

# init cloudformation session
session = boto3.Session(profile_name='nicor88-aws-dev')
cfn = session.client('cloudformation')

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'dev_config.yml'))

STACK_NAME = cfg['lambda']['stack_name']

template = Template()
description = 'Dev Lambdas'
template.add_description(description)
# AWSTemplateFormatVersion
template.add_version('2010-09-09')

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'DevLambdas'
        }
    ]
}

cfn.validate_template(TemplateBody=template_json)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
