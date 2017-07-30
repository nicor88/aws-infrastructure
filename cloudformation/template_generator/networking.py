import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml
import os

from troposphere import ec2
from troposphere import GetAtt, Output, Parameter, Ref, Tags, Template

import cloudformation.utils as utils

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'networking_config.yml'))

STACK_NAME = cfg['stack_name']

template = Template()
description = 'Stack containing Networking Resources'
template.add_description(description)
template.add_version('2010-09-09')


generic_ec2_public_subnet = template.add_resource(
    ec2.Subnet(
        'EC2PublicSubnet',
        AvailabilityZone=cfg['default_subnet_availability_zone'],
        CidrBlock='172.31.1.0/24',
        VpcId=cfg['vpc_id'],
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            AZ=cfg['region'],
            Name='generic-ec2-public-subnet'
        )
    )
)

template.add_resource(
    ec2.SubnetRouteTableAssociation('GenericEC2SubnetRouteTableAssociation',
                                    RouteTableId=cfg['public_route_table'],
                                    SubnetId=Ref(generic_ec2_public_subnet)
                                    )
)

generic_emr_subnet = template.add_resource(
    ec2.Subnet(
        'GenericEMRSubnet',
        AvailabilityZone=cfg['default_subnet_availability_zone'],
        CidrBlock='172.31.2.0/24',
        VpcId=cfg['vpc_id'],
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            AZ=cfg['region'],
            Name='generic-emr-public-subnet'
        )
    )
)

template.add_resource(
    ec2.SubnetRouteTableAssociation('GenericEMRSubnetRouteTableAssociation',
                                    RouteTableId=cfg['public_route_table'],
                                    SubnetId=Ref(generic_emr_subnet)
                                    )
)

jupyter_emr_subnet = template.add_resource(
    ec2.Subnet(
        'JupyterEMRSubnet',
        AvailabilityZone=cfg['default_subnet_availability_zone'],
        CidrBlock='172.31.3.0/24',
        VpcId=cfg['vpc_id'],
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            AZ=cfg['region'],
            Name='jupyter-emr-public-subnet'
        )
    )
)

template.add_resource(
    ec2.SubnetRouteTableAssociation('JupyterEMRSubnetRouteTableAssociation',
                                    RouteTableId=cfg['public_route_table'],
                                    SubnetId=Ref(jupyter_emr_subnet)
                                    )
)

# Security groups
all_ssh_security_group = template.add_resource(
    ec2.SecurityGroup(
        'AllSSH',
        VpcId=cfg['vpc_id'],
        GroupDescription='Allow SSH traffic from Everywhere',
        SecurityGroupIngress=[
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='22',
                ToPort='22',
                CidrIp='0.0.0.0/0'
            )
        ],
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            Name='all-ssh-sg'
        )
    )
)

master_security_group = template.add_resource(
    ec2.SecurityGroup(
        'EMRMasterSecurityGroup',
        VpcId=cfg['vpc_id'],
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
            Name='emr-master-sg'
        )
    )
)

# Outputs
template.add_output([
    Output('GenericEC2Subnet',
           Description='Public Subnet for Generic EC2 Instances',
           Value=Ref(generic_ec2_public_subnet)),
    Output('GenericEMRSubnet',
           Description='Public Subnet for Generic EMR Cluster',
           Value=Ref(generic_emr_subnet)),
    Output('JupyterEMRSubnet',
           Description='Public Subnet for Jupyter EMR Cluster',
           Value=Ref(generic_emr_subnet)),
    Output('AllSshSecurityGroup',
           Description='Security group to enable SSH from Everywhere',
           Value=Ref(all_ssh_security_group)),
    Output('EMRMasterSecurityGroup',
           Description='Security group to enable some app ports for Master Node',
           Value=Ref(master_security_group)),
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'Networking'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
