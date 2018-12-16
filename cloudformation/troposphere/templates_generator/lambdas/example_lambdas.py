import base64

from awacs.aws import Statement, Allow, Action
import boto3
from troposphere import awslambda, iam
from troposphere import Template, Output, Ref, GetAtt, Parameter

import cloudformation.troposphere.utils as utils

kms = boto3.client('kms')


def encrypt(*, kms_alias, value):
    aliases = kms.list_aliases()['Aliases']
    key_id = [a['TargetKeyId'] for a in aliases if a['AliasName'] == 'alias/'+kms_alias][0]
    encrypted = kms.encrypt(KeyId=key_id, Plaintext=value)
    return base64.b64encode(encrypted['CiphertextBlob']).decode()


STACK_NAME = 'ExampleLambdasStack'

template = Template()
description = 'Collection of Lambda Function'
template.add_description(description)
template.add_version('2010-09-09')


kms_arn = template.add_parameter(
    Parameter(
        'KMSArn',
        Type='String',
        Description='KMS arn used inside the lambda',
    )
)

lambda_execution_role = template.add_resource(
    iam.Role(
        'ExecutionRole',
        RoleName=f'ExecutionRole-{STACK_NAME}',
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
            iam.Policy(
                PolicyName='KMS',
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        Statement(
                            Sid='Kms',
                            Effect=Allow,
                            Action=[
                                Action('kms', '*')
                            ],
                            Resource=["*"]
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
        FunctionName='hello_world',
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

hello_world_with_enc_vars_lambda = template.add_resource(
    awslambda.Function(
        'HelloWorldEncVarsFunction',
        FunctionName='hello_world_enc_vars',
        Description='Hello world lambdas with encrypted vars Python 3.6',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('ExecutionRole', 'Arn'),
        KmsKeyArn=Ref(kms_arn),
        Code=awslambda.Code(
            S3Bucket='nicor-dev',
            S3Key='deployments/lambdas/travis_build/hello_world.zip',
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128,
        Environment=awslambda.Environment('LambdaVars',
                                          Variables=
                                          {'SAMPLE_VAR': encrypt(kms_alias='nicor88-key', value='test')
                                           #replace with something from secret env
                                           })
    )
)

# utils.add_lambda_scheduler(template_res=template,
#                            lambda_function_name='hello_world',
#                            lambda_function_arn=GetAtt(hello_world_lambda, 'Arn'),
#                            cron='cron(0/5 * * * ? *)'
#                            )

template.add_output([
    Output('LambdaExecutionRole',
           Description='Lambdas Execution role',
           Value=Ref(lambda_execution_role)),

    Output('HelloWorldLambda',
           Description='HelloWorld Lambda Function',
           Value=Ref(hello_world_lambda)),
    Output('HelloWorldLambdaArn',
           Description='HelloWorld Arn of Lambda Function',
           Value=GetAtt(hello_world_lambda, 'Arn')),

])

template_json = template.to_json(indent=4)
# print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Capabilities': [
        'CAPABILITY_IAM',
        'CAPABILITY_NAMED_IAM'
    ],
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'HelloWorldLambda'
        }
    ],
    'Parameters': [
        {
            'ParameterKey': 'KMSArn',
            'ParameterValue': 'arn:aws:kms:eu-west-1:749785218022:key/200b88fb-2535-4736-9704-141b0bd1462f',
        }
    ],
    'NotificationARNs': [
        'arn:aws:sns:eu-west-1:749785218022:cloudformation'
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
