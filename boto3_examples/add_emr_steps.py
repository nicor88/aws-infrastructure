import emr.utils.steps as steps
import cloudformation.utils as utils


def add_steps_with_termination(*, cluster_id):
    # step1
    step_1 = ['/home/hadoop/steps/example_save_as_parquet.py']
    steps.spark_submit(cluster_id=cluster_id, step_name='JSON to Parquet - Step 1', args=step_1)

    # step 2
    step_2 = ['/home/hadoop/steps/example_save_as_parquet.py']
    steps.spark_submit(cluster_id=cluster_id, step_name='JSON to Parquet - Step 2', args=step_2)

    # add step to terminate the cluster
    terminate_cluster = ['/home/hadoop/miniconda/bin/python', '/home/hadoop/steps/delete_cfn_stack.py',
            '--stack-name', 'GenericEMRStack']
    steps.send_command(cluster_id=cluster_id, step_name='Delete CFN stack', args=terminate_cluster)

# example
cluster = utils.get_cluster_id(stack_name='GenericEMRStack')
add_steps_with_termination(cluster_id=cluster)
