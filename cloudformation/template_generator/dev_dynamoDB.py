import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import dynamodb2
from troposphere import Template, Tags, Output, Ref, Parameter

# init cloudformation session
session = boto3.Session(profile_name='nicor88-aws-dev')
cfn = session.client('cloudformation')

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'dev_dynamo.yml'))

STACK_NAME = cfg['dynamo']['stack_name']

template = Template()
description = 'Dev Dynamo Table'
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
            'Value': 'DevDynamo'
        }
    ]
}

cfn.validate_template(TemplateBody=template_json)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
