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
        MaxValue='40'
    ))


emr_subnet = template.add_resource(
    ec2.Subnet(
        'EMRSubet',
        AvailabilityZone=cfg['network']['subnet_availability_zone'],
        CidrBlock=cfg['network']['subnet_cidr_block'],
        VpcId=cfg['network']['vpc_id'],
        MapPublicIpOnLaunch=True,  #TODO change this after a better design of network stack
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            AZ=cfg['region'],
            Name='jupyter-emr-subnet'
        )
    )
)

template.add_resource(
    ec2.SubnetRouteTableAssociation('DevPublicSubnetRouteTableAssociation',
                                    RouteTableId=cfg['network']['public_route_table'],
                                    SubnetId=Ref(emr_subnet)
                                    )
)

# master security group
master_security_group = template.add_resource(
    ec2.SecurityGroup(
        'EMRMasterSecurityGroup',
        VpcId=cfg['network']['vpc_id'],
        GroupDescription='Enable Apps port for Master Node',
        SecurityGroupIngress=[
            # enable ssh
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='22',
                ToPort='22',
                CidrIp='0.0.0.0/0'
            ),
            # enable port 80 for Ganglia
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='80',
                ToPort='80',
                CidrIp='0.0.0.0/0'
            ),
            # enable Spark DAG
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='8088',
                ToPort='8088',
                CidrIp='0.0.0.0/0'
            ),
            # enable Spark History
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='18080',
                ToPort='18080',
                CidrIp='0.0.0.0/0'
            ),
            # enable Jupyter Port
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='8888',
                ToPort='8888',
                CidrIp='0.0.0.0/0'
            )
        ],
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            Name='jupyter-emr-master-sg'
        )
    )
)

cluster = template.add_resource(emr.Cluster(
    'Cluster',
    Name='Jupyter Cluster',
    ReleaseLabel=cfg['version'],
    JobFlowRole='GenericEMRInstanceProfile',
    ServiceRole='GenericEMRServiceRole',
    Instances=emr.JobFlowInstancesConfig(
        Ec2KeyName=cfg['ssh_key'],
        Ec2SubnetId=Ref(emr_subnet),
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
        AdditionalMasterSecurityGroups=[Ref(master_security_group)],
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
