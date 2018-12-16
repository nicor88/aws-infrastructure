from pkg_resources import resource_string

import boto3
import yaml
from troposphere import Template

import cloudformation.troposphere.utils as utils

# load config
cfg = yaml.load(resource_string('config', 'dev_config.yml'))

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

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
