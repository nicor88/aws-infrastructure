import emr.utils.steps as steps
import cloudformation.utils as utils

# example
cluster_id = utils.get_cluster_id(stack_name='GenericEMRStack')
args = ['/home/hadoop/steps/example_save_as_parquet.py', 'arg1']
steps.spark_submit(cluster_id=cluster_id, step_name='JSON to Parquet', args=args)
