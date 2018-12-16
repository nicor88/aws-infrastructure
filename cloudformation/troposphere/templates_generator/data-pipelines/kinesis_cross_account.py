import os
import boto3
from pkg_resources import resource_string
import yaml

from troposphere import awslambda, iam, kinesis
from troposphere import Template, Output, Ref, GetAtt
from awacs.aws import Statement, Allow, Action

import cloudformation.troposphere.utils as utils

cfg = yaml.load(resource_string('config', 'kinesis_cross_account_cfg.yml'))

STACK_NAME = cfg['stack_name']

template = Template()
description = 'Stack containing kinesis and a lambda writing to another account'
template.add_description(description)
template.add_version('2010-09-09')

kinesis_stream = template.add_resource(
    kinesis.Stream('DevStream',
                   Name=cfg['kinesis']['stream_name'],
                   ShardCount=cfg['kinesis']['shard_count']
                   )
)

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
                        ),
                        Statement(
                            Sid='AssumeRole',
                            Effect=Allow,
                            Action=[
                                Action('iam', 'PassRole'),
                                Action('iam', 'GenerateCredentialReport'),
                                Action('iam', 'Get*'),
                                Action('iam', 'List*'),
                            ],
                            Resource=['*']
                        ),
                        Statement(
                            Sid='PassRole',
                            Effect=Allow,
                            Action=[
                                Action('sts', 'AssumeRole')
                            ],
                            Resource=[cfg['cross_account_role'].format(os.environ['CROSS_ACCOUNT'])]
                        ),
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

deliver_to_firehose_lambda = template.add_resource(
    awslambda.Function(
        'DeliverToFirehoseLambda',
        FunctionName=cfg['deliver_to_firehose_lambda']['function_name'],
        Description='Lambda function to read kinesis stream and put to firehose',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('ExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=cfg['deliver_to_firehose_lambda']['deployment_bucket'],
            S3Key=cfg['deliver_to_firehose_lambda']['s3_key'],
        ),
        Runtime=cfg['deliver_to_firehose_lambda']['runtime'],
        Timeout=cfg['deliver_to_firehose_lambda']['timeout'],
        MemorySize=cfg['deliver_to_firehose_lambda']['memory_size'],
        Environment=awslambda.Environment('LambdaVars',
                                          Variables=
                                          {'DELIVERY_STREAM': cfg['firehose_delivery_stream'],
                                           'CROSS_ACCOUNT_ROLE_ARN': cfg['cross_account_role']
                                          .format(os.environ['CROSS_ACCOUNT'])
                                           }
                                          )
    )
)

kinesis_trigger_lambda = template.add_resource(
    awslambda.EventSourceMapping('KinesisLambdaTrigger',
                                 BatchSize=cfg['deliver_to_firehose_lambda']['batch_size'],
                                 Enabled=cfg['deliver_to_firehose_lambda']['enabled'],
                                 FunctionName=Ref(deliver_to_firehose_lambda),
                                 StartingPosition=cfg['deliver_to_firehose_lambda']['kinesis_shard_iterator'],
                                 EventSourceArn=GetAtt(kinesis_stream, 'Arn')
                                 )
)

template.add_output([
    Output('KinesisStream',
           Description='Kinesis stream',
           Value=Ref(kinesis_stream))])

template.add_output([
    Output('KinesisStreamArn',
           Description='Kinesis stream Arn',
           Value=GetAtt(kinesis_stream, 'Arn'))])

template.add_output([
    Output('LambdaExecutionRole',
           Description='Execution role of the lambda function',
           Value=Ref(lambda_execution_role))])

template.add_output([
    Output('DeliverToFirehoseLambda',
           Description='Lambda to put kinesis records to a firehose'
                       ' that belongs to another account',
           Value=Ref(deliver_to_firehose_lambda))])


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

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
