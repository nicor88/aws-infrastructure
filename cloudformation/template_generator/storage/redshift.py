import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml
import os

from troposphere import GetAtt, Join, Output, Parameter, Ref, Tags, Template
import troposphere.redshift as redshift

from troposphere.constants import SUBNET_ID

import cloudformation.utils as utils

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'boilerplate_config.yml'))
networking_resources = utils.get_stack_resources(stack_name='NetworkingStack')

STACK_NAME = 'Storage-Redshift-Stack'

template = Template()
description = 'Description for the stack'
template.add_description(description)
template.add_version('2010-09-09')

master_user = template.add_parameter(
    Parameter(
        'MasterUser',
        Type='String',
        Description='Master User for Redshift Cluster',
    )
)

master_user_password = template.add_parameter(
    Parameter(
        'MasterUserPassword',
        Type='String',
        Description=' Master User Password for Redshift Cluster',
    )
)

subnet = template.add_parameter(
    Parameter(
        'Subnet',
        Type=SUBNET_ID,
        Description='Subnet to use for Redshift',
    )
)

security_group = template.add_parameter(
    Parameter(
        'SecurityGroup',
        Type='String',
        Description='Security Group to use for Redshift',
    )
)

# TODO add a IAM role to access S3

redshift_cluster = template.add_resource(
    redshift.Cluster('RedshiftCluster',
                     ClusterType='single-node',  # TODO try 'multi-node'
                     ClusterSubnetGroupName=Ref(subnet),
                     VpcSecurityGroupIds=[Ref(security_group)],
                     DBName='dev',
                     MasterUsername=Ref(master_user),
                     PubliclyAccessible=True,
                     MasterUserPassword=Ref(master_user_password),
                     NodeType='dc1.large',
                     DeletionPolicy='Snapshot',
                     )
)

# Outputs
template.add_output([
    Output('RedshiftCluster',
           Description='Redshift Cluster',
           Value=Ref(redshift_cluster)),
    Output('RedshiftClusterEndpoint',
           Value=Join(':', [GetAtt(redshift_cluster, 'Endpoint.Address'),
                            GetAtt(redshift_cluster, 'Endpoint.Port')]),
           )
])


template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Parameters': [
        {
            'ParameterKey': 'Subnet',
            'ParameterValue': networking_resources['GenericEC2Subnet'],
        },
        {
            'ParameterKey': 'SecurityGroup',
            'ParameterValue': networking_resources['RedshiftSecurityGroup'],
        },
        {
            'ParameterKey': 'MasterUser',
            'ParameterValue': 'nicor88',
        },
        {
            'ParameterKey': 'MasterUserPassword',
            'ParameterValue': os.environ['REDSHIFT_MASTER_PASSWORD'],
        },
    ],
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'BoilerplateTemplate'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
