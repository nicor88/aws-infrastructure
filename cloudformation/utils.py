import cfn_flip
import logging
import boto3
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


def get_cluster_id(*,stack_name, ClusterResourceName='Cluster'):
    cfn = boto3.client('cloudformation')
    try:
        cluster = cfn.describe_stack_resource(StackName=stack_name,
                                             LogicalResourceId=ClusterResourceName)['StackResourceDetail']
        cluster_id = cluster['PhysicalResourceId']
        return cluster_id
    except Exception as e:
        raise e
