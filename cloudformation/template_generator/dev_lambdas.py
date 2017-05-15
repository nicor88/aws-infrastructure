import os
import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import awslambda, iam
from troposphere.cloudformation import AWSCustomObject
from awacs.aws import Statement, Allow, Deny, Policy, Action, Condition
from troposphere import Template, Tags, Output, Ref, Parameter, GetAtt

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'dev_config.yml'))

# setup aws session
os.environ['AWS_DEFAULT_REGION'] = cfg['region']
os.environ['AWS_PROFILE'] = 'nicor88-aws-dev'
cfn = boto3.client('cloudformation')

STACK_NAME = cfg['lambda']['stack_name']

template = Template()
description = 'Dev Lambdas'
template.add_description(description)
# AWSTemplateFormatVersion
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

hello_world_lambda = template.add_resource(
    awslambda.Function(
        'HelloWorld',
        FunctionName='hello_world',
        Description='Hello world lambdas with Python 3.6',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('ExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=cfg['s3_deployment_bucket'],
            S3Key='deployments/lambdas/hello_world.zip',
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

hello_world_lambda_version = template.add_resource(
    awslambda.Version(
        'HelloWorldLambdaVersion',
        Description='Version of the Lambda',
        FunctionName=Ref(hello_world_lambda)
    )
)

hello_world_lambda_alias = template.add_resource(
    awslambda.Alias(
        'HelloWorldLambdaAlias',
        FunctionName=Ref(hello_world_lambda),
        FunctionVersion=GetAtt(hello_world_lambda_version, 'Version'),
        Name='LIVE'

    )
)


# test to see if a lambda function can be triggered with a custom
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
            S3Bucket=cfg['s3_deployment_bucket'],
            S3Key='deployments/lambdas/custom_resource.zip',
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

custom_resource_test_lambda_version = template.add_resource(
    awslambda.Version(
        'CustomResourceLambdaVersion',
        Description='Version of the Lambda',
        FunctionName=Ref(custom_resource_test_lambda)
    )
)

custom_resource_test_lambda_alias = template.add_resource(
    awslambda.Alias(
        'CustomResourceLambdaAlias',
        FunctionName=Ref(custom_resource_test_lambda),
        FunctionVersion=GetAtt(custom_resource_test_lambda_version, 'Version'),
        Name='LIVE'

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
            'Value': 'DevLambdas'
        }
    ]
}

cfn.validate_template(TemplateBody=template_json)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
