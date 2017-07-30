import boto3

from troposphere import logs
from troposphere import GetAtt, Output, Parameter, Ref, Tags, Template

import cloudformation.utils as utils

STACK_NAME = 'LogsStack'

template = Template()
description = 'Stack containing EMR with conda in all nodes'
template.add_description(description)
template.add_version('2010-09-09')

generic_emr_log_group = template.add_resource(logs.LogGroup('GenericEMR',
                                                            LogGroupName='/emr/generic_cluster/apps',
                                                            )
                                              )
# Outputs
template.add_output([
    Output("GenericEMRLogGroup",
           Description="Log Group for Generic EMR",
           Value=Ref(generic_emr_log_group)),
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Capabilities': [
        'CAPABILITY_IAM',
    ],
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'Logs'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
