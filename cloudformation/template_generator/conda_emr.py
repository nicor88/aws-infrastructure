import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import ec2
from troposphere import Ref, Tags, Template

import cloudformation.utils as utils

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'conda_emr_config.yml'))

STACK_NAME = cfg['stack_name']

template = Template()
description = 'Stack containing EMR with conda in all nodes'
template.add_description(description)
template.add_version('2010-09-09')

conda_emr_subnet = template.add_resource(
    ec2.Subnet(
        'CondaEMRSubet',
        AvailabilityZone='eu-west-1a',
        CidrBlock='172.31.2.0/24',
        VpcId=cfg['network']['vpc_id'],
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            AZ=cfg['region'],
            Name='conda-emr-subnet'
        )
    )
)

template.add_resource(
    ec2.SubnetRouteTableAssociation('DevPublicSubnetRouteTableAssociation',
                                    RouteTableId=cfg['network']['public_route_table'],
                                    SubnetId=Ref(conda_emr_subnet)
                                    )
)


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
            'Value': 'CondaEMR'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
