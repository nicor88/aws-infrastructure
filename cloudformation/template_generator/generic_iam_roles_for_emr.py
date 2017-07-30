import boto3

from awacs.aws import Action, Allow, Statement
from troposphere import iam
from troposphere import GetAtt, Output, Ref, Template

import cloudformation.utils as utils

STACK_NAME = 'GenericIAMRolesForEMR'

# ----- Template ----- #
template = Template()
description = 'Stack containing Generic IAM roles for EMR'
template.add_description(description)
template.add_version('2010-09-09')


# IAM roles required by EMR

# emr service role used during the creation of the cluster
emr_service_role = template.add_resource(
    iam.Role(
        'EMRServiceRole',
        RoleName='GenericEMRServiceRole',
        AssumeRolePolicyDocument={
            'Statement': [{
                'Effect': 'Allow',
                'Principal': {
                    'Service': [
                        'elasticmapreduce.amazonaws.com'
                    ]
                },
                'Action': ['sts:AssumeRole']
            }]
        },
        ManagedPolicyArns=[
            'arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole'
        ]
    ))

# instance profile role
# role assumed by the ec2 instances
emr_job_flow_role = template.add_resource(
    iam.Role(
        'EMRJobFlowRole',
        RoleName='GenericEMRJobFlowRole',
        AssumeRolePolicyDocument={
            'Statement': [{
                'Effect': 'Allow',
                'Principal': {
                    'Service': [
                        'ec2.amazonaws.com'
                    ]
                },
                'Action': ['sts:AssumeRole']
            }]
        },
        Policies=[
            iam.Policy(
                PolicyName='GrantLogs',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        Statement(
                            Effect=Allow,
                            Action=[
                                Action('logs', '*'),
                            ],
                            Resource=["arn:aws:logs:*:*:*"]
                        ),
                    ]
                }),
            iam.Policy(
                PolicyName='GrantS3',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        Statement(
                            Effect=Allow,
                            Action=[
                                Action('s3', '*'),
                            ],
                            Resource=["*"]
                        ),
                    ]
                }),
            # TODO to remove just to try
            iam.Policy(
                PolicyName='CfnAccess',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        Statement(
                            Effect=Allow,
                            Action=[
                                Action('cloudformation', '*')
                            ],
                            Resource=[
                                'arn:aws:cloudformation:eu-west-1:*:stack/GenericEMRStack/*'
                            ]
                        ),
                    ]
                }),
            # TODO to remove just to try
            iam.Policy(
                PolicyName='FullEc2Access',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        Statement(
                            Effect=Allow,
                            Action=[
                                Action('ec2', '*')
                            ],
                            Resource=[
                                '*'
                            ]
                        ),
                    ]
                }),
            # TODO to remove just to try
            iam.Policy(
                PolicyName='FullEMRAccess',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        Statement(
                            Effect=Allow,
                            Action=[
                                Action('elasticmapreduce', '*')
                            ],
                            Resource=[
                                '*'
                            ]
                        ),
                    ]
                }),
        ],
        # ManagedPolicyArns=[
        #     'arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role'
        # ]
    ))

emr_instance_profile = template.add_resource(
    iam.InstanceProfile(
        'EMRInstanceProfile',
        InstanceProfileName='GenericEMRInstanceProfile',
        Roles=[Ref(emr_job_flow_role)],
    ))

# Output
template.add_output([
    Output('EMRServiceRole',
           Value=Ref(emr_service_role),
           Description='Service role needed by EMR'
           ),
    Output('EMRInstanceProfile',
           Value=Ref(emr_instance_profile),
           Description='Instance profile for nodes in EMR cluster'
           ),
    Output('EMRJobFlowRole',
           Value=Ref(emr_job_flow_role),
           Description='Job Flow role needed by EMR'
           ),
    Output('EMRInstanceProfileArn',
           Value=GetAtt(emr_instance_profile, 'Arn'),
           Description='ARN of Instance profile for nodes in EMR cluster'
           ),
]
)

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template.to_json(indent=4),
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'GenericIAMRolesForEMR'
        }
    ],
    'Capabilities': [
        'CAPABILITY_IAM',
        'CAPABILITY_NAMED_IAM'
    ],
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
