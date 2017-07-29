import boto3
cfn = boto3.client('cloudformation')

stack_name = 'GenericEMRStack'

# get the created cluster id
resources = cfn.describe_stack_resources(StackName=stack_name)['StackResources']
cluster_id = cfn.describe_stack_resource(StackName=stack_name,
                                         LogicalResourceId='Cluster')['StackResourceDetail'][
    'PhysicalResourceId']
