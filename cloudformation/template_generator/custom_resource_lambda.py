import os
import boto3

from troposphere import awslambda, iam
from troposphere.cloudformation import AWSCustomObject
from awacs.aws import Statement, Allow, Action
from troposphere import Template, Output, Ref, GetAtt

import cloudformation.utils as utils

# setup aws session
os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'
os.environ['AWS_PROFILE'] = 'nicor88-aws-dev'
cfn = boto3.client('cloudformation')

STACK_NAME = 'CustomResourceLambdaStack'

template = Template()
description = 'Dev Lambdas'
template.add_description(description)
template.add_version('2010-09-09')

# execution role for lambdas
lambda_execution_role = template.add_resource(
    iam.Role(
        'ExecutionRole',
        Path='/',
        Policies=[
            iam.Policy(
                PolicyName='GrantLogs',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        Statement(
                            Sid='Logs',
                            Effect=Allow,
                            Action=[
                                Action('logs', 'CreateLogGroup'),
                                Action('logs', 'CreateLogStream'),
                                Action('logs', 'PutLogEvents')
                            ],
                            Resource=["arn:aws:logs:*:*:*"]
                        ),
                    ]
                }),
        ],
        AssumeRolePolicyDocument={
            "Version": "2012-10-17",
            "Statement": [
                {"Action": ["sts:AssumeRole"],
                 "Effect": "Allow",
                 "Principal": {"Service": ["lambda.amazonaws.com"]}
                 }
            ]},
    ))


class CustomResource(AWSCustomObject):
    resource_type = "Custom::CustomResourceTest"

    props = {
        'ServiceToken': (str, True)
    }

custom_resource_test_lambda = template.add_resource(
    awslambda.Function(
        'CustomResourceLambda',
        FunctionName='custom_resource',
        Description='Custom Resource Test lambda with Python 3.6',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('ExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket='nicor-dev',
            S3Key='deployments/lambdas/travis_build/custom_resource.zip',
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

custom_resource = template.add_resource(
    CustomResource('CustomResource',
                   DependsOn='CustomResourceLambda',
                   ServiceToken=GetAtt(custom_resource_test_lambda, 'Arn')
                   )
)

template.add_output([
    Output('LambdaExecutionRole',
           Description='Lambdas Execution role',
           Value=Ref(lambda_execution_role))])

template.add_output([
    Output('CustomResourcePurpose',
           Description='Custom Purpose setup by the lambda function',
           Value=GetAtt('CustomResource', 'Purpose')
           )])

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
            'Value': 'CustomResourceLambda'
        }
    ]
}

cfn.validate_template(TemplateBody=template_json)

utils.write_template(**stack_args)
# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
