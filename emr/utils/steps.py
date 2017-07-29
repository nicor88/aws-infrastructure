import boto3
import logging

logger = logging.getLogger(__name__)


def send_command():
    raise NotImplementedError


def spark_submit(*, cluster_id, args, step_name='Spark Submit Job'):
    emr = boto3.client('emr')
    # description cluster
    desc = emr.describe_cluster(ClusterId=cluster_id)
    logger.info('Adding step to cluster {} {}'.format(cluster_id,
                                                      desc.get('Cluster', {}).get('Name')))

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
    logger.info(step_example_with_params)

    response = emr.add_job_flow_steps(JobFlowId=cluster_id,
                                      Steps=[step_example_with_params])
    return response
