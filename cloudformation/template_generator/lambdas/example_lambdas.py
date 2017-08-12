import boto3

from troposphere import awslambda, iam
from awacs.aws import Statement, Allow, Action
from troposphere import Template, Output, Ref, GetAtt


import cloudformation.utils as utils

STACK_NAME = 'ExampleLambdasStack'

template = Template()
description = 'Collection of Lambda Function'
template.add_description(description)
template.add_version('2010-09-09')

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
        'HelloWorldFunction',
        FunctionName='HelloWorld',
        Description='Hello world lambdas with Python 3.6',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('ExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket='nicor-dev',
            S3Key='deployments/lambdas/travis_build/hello_world.zip',
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128
    )
)

utils.add_lambda_scheduler(template_res=template,
                           lambda_function_name='HelloWorld',
                           lambda_function_arn=GetAtt(hello_world_lambda, 'Arn'),
                           cron='cron(0/5 * * * ? *)'
                           )

template.add_output([
    Output('LambdaExecutionRole',
           Description='Lambdas Execution role',
           Value=Ref(lambda_execution_role))])

template_json = template.to_json(indent=4)
# print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Capabilities': [
        'CAPABILITY_IAM',
    ],
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'HelloWorldLambda'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
