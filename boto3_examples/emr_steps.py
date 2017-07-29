import boto3

emr = boto3.client('emr')


def spark_submit(*, cluster_id, args, step_name):
    # description cluster
    desc = emr.describe_cluster(ClusterId=cluster_id)
    print('Adding step to', cluster_id, ':', desc.get('Cluster', {}).get('Name'))

    all_args = ['spark-submit',
                '--deploy-mode',
                'client',
                '--master',
                'yarn'
                ]
    all_args.extend(args)

    step_example_with_params = {'ActionOnFailure': 'CONTINUE',
                                'HadoopJarStep': {'Args': all_args,
                                                  'Jar': 'command-runner.jar'},
                                'Name': step_name}
    print(step_example_with_params)

    response = emr.add_job_flow_steps(JobFlowId=cluster_id,
                                      Steps=[step_example_with_params])
    return response

# example
cluster_id = 'your_cluster_id'
args = ['/home/hadoop/tasks/to_execute.py', 'arg1', 'arg2']

spark_submit(cluster_id=cluster_id, step_name='Execute Steps', args=args)
