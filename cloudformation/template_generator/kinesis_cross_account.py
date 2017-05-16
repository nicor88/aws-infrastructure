import os
import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import awslambda, iam, kinesis, firehose, s3
from troposphere import Template, Tags, Output, Ref, Parameter, GetAtt
from awacs.aws import Statement, Allow, Deny, Policy, Action, Condition

# setup aws session
os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'
os.environ['AWS_PROFILE'] = 'nicor88-aws-dev'
cfn = boto3.client('cloudformation')

# TODO configs needs to come froma  file
STACK_NAME = 'KinesisCrossAccountStack'
KINESIS_STREAM_NAME = 'EventsStreamSimulation'
KINESIS_SHARD_COUNT = 2

FIREHOSE_DELIVERY_STREAM = 'DeliveryStreamTest'

LAMBDA_FUNCTION_NAME = 'deliver_to_firehose'
S3_DEPLOYMENT_BUCKET = 'nicor-dev'
S3_KEY_LAMBDA = 'deployments/lambdas/deliver_to_firehose.zip'
LAMBDA_BATCH_SIZE = 1000
LAMBDA_ENABLED = False
LAMBDA_MEMORY_SIZE = 128
LAMBDA_TIMEOUT = 30
KINESIS_SHARD_ITERATOR_TYPE = 'TRIM_HORIZON'
CROSS_ACCOUNT_ROLE_ARN = 'arn:aws:iam::755248034388:role/firehose-cross-account-access-role'
# e.g.'arn:aws:iam::755248034388:role/firehose-cross-account-access-role'


template = Template()
description = 'Stack containing kinesis and a lambda writing to another account'
template.add_description(description)
# AWSTemplateFormatVersion
template.add_version('2010-09-09')

kinesis_stream = template.add_resource(
    kinesis.Stream('DevStream',
                   Name=KINESIS_STREAM_NAME,
                   ShardCount=KINESIS_SHARD_COUNT
                   )
)

# lambda section
lambda_execution_role = template.add_resource(
    iam.Role(
        'ExecutionRole',
        Path='/',
        Policies=[
            iam.Policy(
                PolicyName='KinesisToFirehosePolicy',
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
                            Resource=['arn:aws:logs:*:*:*']
                        ),
                        Statement(
                            Sid='KinesisStream',
                            Effect=Allow,
                            Action=[
                                Action('kinesis', '*'),
                            ],
                            Resource=[GetAtt(kinesis_stream, 'Arn')]
                        )
                    ]
                }
            )
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


lambda_stream_to_firehose = template.add_resource(
    awslambda.Function(
        'KinesisStreamToFirehose',
        FunctionName=LAMBDA_FUNCTION_NAME,
        Description='Lambda function to read kinesis stream and put to firehose',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('ExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=S3_DEPLOYMENT_BUCKET,
            S3Key=S3_KEY_LAMBDA,
        ),
        Runtime='python3.6',
        Timeout=LAMBDA_TIMEOUT,
        MemorySize=LAMBDA_MEMORY_SIZE,
        Environment=awslambda.Environment('LambdaVars',
                                          Variables=
                                          {'DELIVERY_STREAM': FIREHOSE_DELIVERY_STREAM,
                                           'CROSS_ACCOUNT_ROLE_ARN': CROSS_ACCOUNT_ROLE_ARN})
    )
)

add_kinesis_trigger_for_lambda = template.add_resource(
    awslambda.EventSourceMapping('KinesisLambdaTrigger',
                                 BatchSize=LAMBDA_BATCH_SIZE,
                                 Enabled=LAMBDA_ENABLED,
                                 FunctionName=LAMBDA_FUNCTION_NAME,
                                 StartingPosition=KINESIS_SHARD_ITERATOR_TYPE,
                                 EventSourceArn=GetAtt(kinesis_stream, 'Arn')
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
            'Value': 'StreamExamples'
        }
    ]
}

cfn.validate_template(TemplateBody=template_json)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
