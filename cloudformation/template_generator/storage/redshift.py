import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml
import os

from troposphere import GetAtt, Join, Output, Parameter, Ref, Template
from troposphere import iam
from awacs import s3 as s3_doc
from awacs.aws import Statement, Allow, Policy, Action
import troposphere.redshift as redshift

from troposphere.constants import SUBNET_ID

import cloudformation.utils as utils

networking_resources = utils.get_stack_resources(stack_name='NetworkingStack')

STACK_NAME = 'Storage-Redshift-Stack'

template = Template()
description = 'Storage Stack containing a Redshift Cluster'
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

policy_doc = Policy(
    Statement=[
        Statement(
            Sid='ReadAccessS3',
            Effect=Allow,
            Action=[Action('s3', 'List*'),
                    Action('s3', 'Get*')
                    ],
            Resource=[
                s3_doc.ARN('nicor-data'),
                s3_doc.ARN('nicor-data/*')
            ]
        ),
    ]
)

redshift_role = template.add_resource(
    iam.Role(
        'RedshiftRole',
        RoleName='RedshiftRole',
        AssumeRolePolicyDocument={
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": [
                        "redshift.amazonaws.com"
                    ]
                },
                "Action": ["sts:AssumeRole"]
            }]
        },

        Policies=[
            iam.Policy(
                PolicyName='{}S3Access'.format(STACK_NAME),
                PolicyDocument=policy_doc,
            )
        ]
    ))

redshift_cluster_subnet_group = template.add_resource(
    redshift.ClusterSubnetGroup('RedshiftClusterSubnetGroup',
                                Description='Subnets group for Redshift Cluster',
                                SubnetIds=[Ref(subnet)])
)

redshift_cluster = template.add_resource(
    redshift.Cluster('RedshiftCluster',
                     ClusterType='single-node',  # TODO try 'multi-node'
                     NodeType='dc1.large',
                     ClusterSubnetGroupName=Ref(redshift_cluster_subnet_group),
                     VpcSecurityGroupIds=[Ref(security_group)],
                     PubliclyAccessible=True,
                     DBName='dev',
                     MasterUsername=Ref(master_user),
                     MasterUserPassword=Ref(master_user_password),
                     IamRoles=[GetAtt(redshift_role, 'Arn')],
                     DeletionPolicy='Snapshot',
                     AutomatedSnapshotRetentionPeriod=0  # just for dev mode
                     )
)

# Outputs
template.add_output([
    Output('RedshiftRole',
           Value=Ref(redshift_role),
           Description='Redshift IAM Role',
           ),
    Output('RedshiftRoleArn',
           Value=GetAtt(redshift_role,'Arn'),
           Description='Redshift Arn IAM Role',
           ),
    Output('RedshiftCluster',
           Value=Ref(redshift_cluster),
           Description='Redshift Cluster',
           ),
    Output('RedshiftClusterEndpoint',
           Value=Join(':', [GetAtt(redshift_cluster, 'Endpoint.Address'),
                            GetAtt(redshift_cluster, 'Endpoint.Port')]),
           Description='Redshift Cluster Endpoint',
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
            'Value': 'Redshift'
        }
    ],
    'Capabilities': [
        'CAPABILITY_NAMED_IAM'
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
