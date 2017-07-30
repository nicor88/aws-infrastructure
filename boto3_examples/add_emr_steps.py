import emr.utils.steps as steps
import cloudformation.utils as utils

# example
cluster_id = utils.get_cluster_id(stack_name='GenericEMRStack')
# args = ['/home/hadoop/steps/example_save_as_parquet.py', 'arg1']
args = ['/home/hadoop/steps/example_save_as_parquet.py']
steps.spark_submit(cluster_id=cluster_id, step_name='JSON to Parquet', args=args)


# TODO before deleting the stack put another step in between doing nothing
# example to delete a stack from emr
# cluster_id = utils.get_cluster_id(stack_name='GenericEMRStack')
# args = ['/home/hadoop/miniconda/bin/python', '/home/hadoop/steps/delete_cfn_stack.py', '--stack-name', 'GenericEMRStack']
# steps.send_command(cluster_id=cluster_id, step_name='Delete CFN stack', args=args)
