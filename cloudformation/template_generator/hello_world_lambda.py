import os
import boto3

from troposphere import awslambda, iam
from awacs.aws import Statement, Allow, Action
from troposphere import Template, Output, Ref, GetAtt
from troposphere.events import Rule, Target

import cloudformation.utils as utils

# setup aws session
os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'
os.environ['AWS_PROFILE'] = 'nicor88-aws-dev'
cfn = boto3.client('cloudformation')

STACK_NAME = 'HelloWorldLambdaStack'

template = Template()
description = 'All needed resources to have a lambda function'
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

hello_world_event_target = Target(
    "HelloWorldEventTarget",
    Arn=GetAtt(hello_world_lambda, 'Arn'),
    Id="HelloWorldFunctionEventTarget"
)

hello_world_scheduler = template.add_resource(
    Rule(
        'ScheduledRule',
        ScheduleExpression='cron(0/5 * * * ? *)', # every 5 minutes
        # http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html
        Description="Scheduled Event for Lambda",
        State="ENABLED",
        Targets=[hello_world_event_target]
    ))

add_permission = template.add_resource(
    awslambda.Permission(
        'AccessLambda',
        Action='lambda:InvokeFunction',
        FunctionName='hello_world',
        Principal='events.amazonaws.com',
        SourceArn=GetAtt('ScheduledRule', 'Arn')
    )
)




template.add_output([
    Output('LambdaExecutionRole',
           Description='Lambdas Execution role',
           Value=Ref(lambda_execution_role))])

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
            'Value': 'HelloWorldLambda'
        }
    ]
}

cfn.validate_template(TemplateBody=template_json)

utils.write_template(**stack_args)
# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
