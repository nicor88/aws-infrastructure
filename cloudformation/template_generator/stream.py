import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import awslambda, iam, kinesis, firehose, s3
from troposphere import Template, Tags, Output, Ref, Parameter, GetAtt
from awacs.aws import Statement, Allow, Deny, Policy, Action, Condition

# init cloudformation session
session = boto3.Session(profile_name='nicor88-aws-dev')
cfn = session.client('cloudformation')

cfg = yaml.load(resource_string('cloudformation.config', 'stream_config.yml'))

STACK_NAME = cfg['stack_name']

template = Template()
description = 'Stack containing kinesis and firehose writing to S3'
template.add_description(description)
# AWSTemplateFormatVersion
template.add_version('2010-09-09')

s3_dev_bucket = template.add_resource(
    s3.Bucket('S3DestinationBucket',
              BucketName=cfg['s3_destination_bucket']
              )
)

kinesis_stream = template.add_resource(
    kinesis.Stream('DevStream',
                   Name=cfg['kinesis_stream_name'],
                   ShardCount='1',
                   Tags=Tags(
                       StackName=Ref('AWS::StackName'),
                       Name='DevStream'
                   )
    )
)

firehose_policy_doc = {
    'Statement': [{
        'Sid': 'S3Access',
        'Effect': 'Allow',
        'Action': [
            's3:ListBucket',
            's3:GetBucketLocation',
            's3:ListAllMyBuckets',
        ],
        'Resource': [
                "arn:aws:s3:::{}".format(cfg['s3_destination_bucket']),
                "arn:aws:s3:::{}/*".format(cfg['s3_destination_bucket'])
            ]
    },
        {
            'Sid': 'Logs',
            'Effect': 'Allow',
            'Action': [
                'logs:PutLogEvents'
            ],
            'Resource': ['*']
        }
    ]
}

firohose_delivery_role = template.add_resource(
    iam.Role(
        'FirehoseRole',
        AssumeRolePolicyDocument={
            'Statement': [{
                'Effect': 'Allow',
                'Principal': {
                    'Service': [
                        'firehose.amazonaws.com'
                    ]
                },
                'Action': ['sts:AssumeRole']
            }]
        },
        Policies=[
            iam.Policy(
                PolicyName='Access',
                PolicyDocument=firehose_policy_doc,
            )
        ]
    ))

kinesis_delivery_stream = template.add_resource(
    firehose.DeliveryStream('DeliveryStream',
                            DeliveryStreamName=cfg['kinesis_delivery_stream_name'],
                            S3DestinationConfiguration=
                            firehose.S3DestinationConfiguration('S3DestinationBucket',
                                                                BucketARN="arn:aws:s3:::{}".format(
                                                                    cfg['s3_destination_bucket']),
                                                                CompressionFormat='UNCOMPRESSED',
                                                                Prefix='deelivery_stream/',
                                                                RoleARN=Ref(firohose_delivery_role),
                                                                BufferingHints=firehose.BufferingHints(
                                                                    'BufferingSetup',
                                                                    IntervalInSeconds=60,
                                                                    # 5 minutes
                                                                    SizeInMBs=5)

                                                                ),

                            )
)


lambda_execution_role = template.add_resource(
    iam.Role(
        'ExecutionRole',
        Path='/',
        Policies=[
            iam.Policy(
                PolicyName='AllNeededPolicy',
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
                            Resource=["arn:aws:logs:*:*:*"]  #TODO restrict
                        ),
                        Statement(
                            Sid='KinesisStream',
                            Effect=Allow,
                            Action=[
                                Action('kinesis', '*'),
                            ],
                            Resource=["arn:aws:kinesis:*:*:*"]  #TODO restrict
                        ),
                        Statement(
                            Sid='DeliveryStream',
                            Effect=Allow,
                            Action=[
                                Action('firehose', '*'),
                            ],
                            Resource=["arn:aws:firehose:*:*:*"] #TODO restrict
                        )
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

lambda_stream_to_firehose = template.add_resource(
    awslambda.Function(
        'KinesisStreamToFirehose',
        FunctionName=cfg['lambda_function_name'],
        Description='Lambda function to read kinesis stream and put to firehose',
        Handler='lambda_function.lambda_handler',
        Role=GetAtt('ExecutionRole', 'Arn'),
        Code=awslambda.Code(
            S3Bucket=cfg['s3_deployment_bucket'],
            S3Key=cfg['s3_key_lambda_stream_to_firehose'],
        ),
        Runtime='python3.6',
        Timeout='30',
        MemorySize=128,
        Environment=awslambda.Environment('LambdaVars',
                                          Variables={'DELIVERY_STREAM': cfg[
                                              'kinesis_delivery_stream_name']})
    )
)

add_kinesis_trigger_for_lambda = template.add_resource(
    awslambda.EventSourceMapping('KinesisLambdaTrigger',
                                 BatchSize=100,
                                 Enabled=False,
                                 FunctionName=cfg['lambda_function_name'],
                                 StartingPosition='TRIM_HORIZON',
                                 EventSourceArn=Ref(kinesis_stream)
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
