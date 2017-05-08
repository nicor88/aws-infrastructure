import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import awslambda, iam
from awacs.aws import Statement, Allow, Deny, Policy, Action, Condition
from troposphere import Template, Tags, Output, Ref, Parameter, GetAtt

# init cloudformation session
session = boto3.Session(profile_name='nicor88-aws-dev')
cfn = session.client('cloudformation')

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'dev_config.yml'))
DEPLOYMENT_BUCKET = 'nicor-dev'

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
            S3Bucket=DEPLOYMENT_BUCKET,
            S3Key='deployments/lambdas/hello_world.zip',
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

template.add_output([
    Output('LambdaExecutionRole',
           Description='Lambdas Execution role',
           Value=Ref(lambda_execution_role))])

template.add_output([
    Output('HelloWorld',
           Description='HelloWorld Lambda function',
           Value=Ref(hello_world_lambda))])

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
