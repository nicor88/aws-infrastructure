import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import GetAtt, Join, Output, Parameter, Ref, Tags, Template

import cloudformation.utils as utils

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'boilerplate_config.yml'))

STACK_NAME = cfg['stack_name']

template = Template()
description = 'Description for the stack'
template.add_description(description)
template.add_version('2010-09-09')

resource = template.add_resource(
    # TODO add some resource
)

# Outputs
template.add_output([
    Output('MyOutput',
           Description='Reference to the resource',
           Value=Ref(resource)),
    Output('MyOutputAtt',
           Description='Reference to the resource attibute',
           Value=GetAtt(resource, 'Resource attribute')),
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'BoilerplateTemplate'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
# utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
