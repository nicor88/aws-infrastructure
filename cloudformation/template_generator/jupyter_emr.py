import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml
import os

from troposphere import ec2
import troposphere.emr as emr
from troposphere import GetAtt, Output, Parameter, Ref, Tags, Template

import cloudformation.utils as utils

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'jupyter_emr_config.yml'))
networking_resources = utils.get_stack_resources(stack_name=cfg['networking_stack_name'])

STACK_NAME = cfg['stack_name']

template = Template()
description = 'Stack containing EMR with Jupyter on Master Node'
template.add_description(description)
template.add_version('2010-09-09')

instances = template.add_parameter(
    Parameter(
        'Instances',
        Type='Number',
        Description='Number of core instances',
        MaxValue='10'
    ))

cluster = template.add_resource(emr.Cluster(
    'Cluster',
    Name='Jupyter Cluster',
    ReleaseLabel=cfg['version'],
    JobFlowRole='GenericEMRInstanceProfile',
    ServiceRole='GenericEMRServiceRole',
    Instances=emr.JobFlowInstancesConfig(
        Ec2KeyName=cfg['ssh_key'],
        Ec2SubnetId=networking_resources['JupyterEMRSubnet'],
        MasterInstanceGroup=emr.InstanceGroupConfigProperty(
            Name='Master Instance',
            InstanceCount='1',
            InstanceType='m4.xlarge',
            Market='ON_DEMAND'
        ),
        CoreInstanceGroup=emr.InstanceGroupConfigProperty(
            Name='Core Instance',
            InstanceCount=Ref(instances),
            InstanceType='m4.xlarge',
            Market='SPOT',
            BidPrice='0.1'
        ),
        AdditionalMasterSecurityGroups=[networking_resources['EMRMasterSecurityGroup']],
        # AdditionalSlaveSecurityGroups=[Ref(emr_additional_slave_sg_param)]
    ),
    LogUri='s3://nicor-dev/logs/emr/jupyter',
    BootstrapActions=[
        emr.BootstrapActionConfig(
            Name='Install and set up Jupyter',
            ScriptBootstrapAction=emr.ScriptBootstrapActionConfig(
                Path='s3://nicor-dev/deployments/emr/bootstrap_actions/bootstrap_jupyter.sh',
                Args=['testemr', 's3://nicor-dev/jupyter-notebooks/']
            )
        )
    ],
    Configurations=[
        emr.Configuration(
            Classification="spark-env",
            Configurations=[
                emr.Configuration(
                    Classification="export",
                    ConfigurationProperties={
                        "PYSPARK_PYTHON": os.path.join('/home/hadoop/miniconda', 'bin/python'),
                        "PYTHONPATH": os.path.join('/home/hadoop/miniconda', 'bin/python') + ":/usr/lib/spark/python/:$PYTHONPATH",
                        "PYSPARK_DRIVER_PYTHON": os.path.join('/home/hadoop/miniconda', 'bin/python'),
                        "SPARK_HOME": "/usr/lib/spark",
                        "PYTHONHASHSEED": "123"
                    }
                )
            ]
        ),
    ],
    Applications=[emr.Application(Name=app) for app in cfg['applications']],
    VisibleToAllUsers='true',
    Tags=Tags(
        Name='jupyter-cluster'
    )
))

# Outputs
template.add_output([
    Output("EMRCluster",
           Description="EMRCluster",
           Value=Ref(cluster)),
    Output("EMRClusterMasterDNS",
           Description="EMRCluster",
           Value=GetAtt(cluster, 'MasterPublicDNS')),
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Parameters': [
        {
            'ParameterKey': 'Instances',
            'ParameterValue': cfg['core_instances']
        }

    ],
    'Capabilities': [
        'CAPABILITY_IAM',
    ],
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'CondaEMR'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
# utils.get_cluster_id(stack_name=STACK_NAME)
