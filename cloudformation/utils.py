import cfn_flip
import logging
import boto3

from troposphere.events import Rule, Target
from troposphere import awslambda
from troposphere import Template, Output, Ref, GetAtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def write_template(**stack_args):
    cfn_json_path = 'cloudformation/templates/json/{}.json'.format(stack_args['StackName'])
    cfn_yaml_path = 'cloudformation/templates/yaml/{}.yml'.format(stack_args['StackName'])
    with open(cfn_json_path, 'wt') as f:
        f.write(stack_args['TemplateBody'])
        logger.info('wrote json template')
    with open(cfn_yaml_path, 'wt') as f:
        f.write(cfn_flip.to_yaml(stack_args['TemplateBody']))
        logger.info('wrote yaml template')


def get_cluster_id(*, stack_name, cluster_name='Cluster'):
    cfn = boto3.client('cloudformation')
    try:
        cluster = cfn.describe_stack_resource(StackName=stack_name,
                                              LogicalResourceId=cluster_name)['StackResourceDetail']
        cluster_id = cluster['PhysicalResourceId']
        return cluster_id
    except Exception as e:
        raise e


def get_stack_resources(*, stack_name):
    cfn = boto3.client('cloudformation')
    stack = cfn.describe_stacks(StackName=stack_name)['Stacks'][0]
    outputs = stack['Outputs']
    resources = {o['OutputKey']: o['OutputValue'] for o in outputs}
    return resources


def add_lambda_scheduler(*, template_res, cron, lambda_function_name, lambda_function_arn):
    event_target = Target(
        f'{lambda_function_name}EventTarget',
        Arn=lambda_function_arn,
        Id=f'{lambda_function_name}FunctionEventTarget'
    )
    scheduler = template_res.add_resource(
        Rule(
            f'ScheduledRule{lambda_function_name}',
            ScheduleExpression=cron,
            # http://docs.aws.amazon.com/AmazonCloudWatch/latest/events/ScheduledEvents.html
            Description=f'Scheduled Event for Lambda {lambda_function_name}',
            State="ENABLED",
            Targets=[event_target]
        ))
    add_permission = template_res.add_resource(
        awslambda.Permission(
            f'AccessLambda{lambda_function_name}',
            Action='lambda:InvokeFunction',
            FunctionName=f'{lambda_function_name}',
            Principal='events.amazonaws.com',
            SourceArn=GetAtt(scheduler, 'Arn')
        )
    )
