import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import ec2
from troposphere import Base64, Join, Output, Parameter, Ref, Tags, Template

from troposphere.cloudformation import Init, InitFile, InitFiles, InitConfig, InitService, \
    InitServices
from troposphere.autoscaling import Metadata

import cloudformation.utils as utils

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'boilerplate_ec2_config.yml'))

STACK_NAME = cfg['ec2']['stack_name']

template = Template()
description = 'Dev Server Stack'
template.add_description(description)
template.add_version('2010-09-09')

# security group
all_ssh = template.add_resource(
    ec2.SecurityGroup(
        'AllSSH',
        VpcId=cfg['network']['vpc_id'],
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
            Name='all-ssh'
        )
    )
)

# subnet
# by default all the subnets are put in the default subnet, that is a public subnet with a route
# to Internet Gatewy
# TODO move this resource to a DevNetworking Stack
dev_public_subnet = template.add_resource(
    ec2.Subnet(
        'DevPublicSubnet',
        AvailabilityZone='eu-west-1a',
        CidrBlock='172.31.1.0/24',
        VpcId=cfg['network']['vpc_id'],
        MapPublicIpOnLaunch=True,
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            AZ=cfg['region'],
            Name='dev-public-subnet'
        )
    )
)

template.add_resource(
    ec2.SubnetRouteTableAssociation('DevPublicSubnetRouteTableAssociation',
                                    RouteTableId=cfg['network']['public_route_table'],
                                    SubnetId=Ref(dev_public_subnet)
                                    )
)


# Define Instance Metadata
instance_metadata = Metadata(
    Init({'config': InitConfig(
        commands={
            'update_yum_packages': {
                'command': 'yum update -y'
            },
            'download_miniconda': {
                'command': 'su - ec2-user -c "wget http://repo.continuum.io/miniconda/Miniconda3-4.3.21-Linux-x86_64.sh -O /home/ec2-user/miniconda.sh"',
            },
            'install_miniconda': {
                 'command': 'su - ec2-user -c "bash /home/ec2-user/miniconda.sh -b -p /home/ec2-user/miniconda"',
            },
            'remove_installer': {
                 'command': 'rm -rf /home/ec2-user/miniconda.sh',
            }
        },
        files=InitFiles({
            # setup .bashrc
            '/home/ec2-user/.bashrc': InitFile(
                content=Join('', [
                             'export PATH="/home/ec2-user/miniconda/bin:$PATH"\n'
                             ]),
                owner='ec2-user',
                mode='000400',
                group='ec2-user'),
            # configure cfn-hup
            '/etc/cfn/cfn-hup.conf': InitFile(
                content=Join('',
                             ['[main]\n',
                              'stack=', Ref('AWS::StackId'),
                              '\n',
                              'region=', Ref('AWS::Region'),
                              '\n',
                              'interval=2',
                              '\n',
                              ]),
                mode='000400',
                owner='root',
                group='root'),
            # setup cfn-auto-reloader
            '/etc/cfn/hooks.d/cfn-auto-reloader.conf': InitFile(
                content=Join('',
                             ['[cfn-auto-reloader-hook]\n',
                              'triggers=post.update\n',
                              'path=Resources.DevServer.Metadata.AWS::CloudFormation::Init\n',
                              'action=/opt/aws/bin/cfn-init -v',
                              ' --stack ',  Ref('AWS::StackId'),
                              ' --resource DevServer',
                              ' --region ', Ref('AWS::Region'),
                              '\n'
                              'runas=root\n',
                              ]
                             )
            )
        }),
        services={
            'sysvinit': InitServices({
                'cfn-hup': InitService(
                    enabled=True,
                    ensureRunning=True,
                    files=[
                        '/etc/cfn/cfn-hup.conf',
                        '/etc/cfn/hooks.d/cfn-auto-reloader.conf'
                    ])
            })}
    )
    })
)

# volume
# volume = template.add_resource(
#     ec2.Volume('DevVolume',
#                AvailabilityZone='eu-west-1a',
#                Size='20',
#                VolumeType='gp2',
#                Tags=Tags(
#                    StackName=Ref('AWS::StackName'),
#                    Name='dev-server-volume',
#                )
#                )
# )

# ec2 instance
ec2_instance = template.add_resource(ec2.Instance(
    'DevServer',
    InstanceType='t2.micro',
    ImageId='ami-d7b9a2b1',  # 2017.03 ami-d7b9a2b1  # after resizing ami-594bab20
    SubnetId=Ref(dev_public_subnet),
    SecurityGroupIds=[Ref(all_ssh)],
    InstanceInitiatedShutdownBehavior='stop',
    Monitoring=True,
    KeyName='nicor88-dev',
    Metadata=instance_metadata,
    # Volumes=[
    #     ec2.MountPoint(VolumeId=Ref(volume), Device='/dev/sdb')
    # ],
    UserData=Base64(
        Join(
            '',
            ['#!/bin/bash -xe\n',

             # cfn-init: install what is specified in the metadata section
             '/opt/aws/bin/cfn-init -v ',
             ' --stack ', Ref('AWS::StackName'),
             ' --resource DevServer',
             ' --region ', Ref('AWS::Region'), '\n',

             # cfn-hup
             # Start up the cfn-hup daemon to listen for changes to the server metadata
             'yum install -y aws-cfn-bootstrap\n',
             '/opt/aws/bin/cfn-hup || error_exit "Failed to start cfn-hup"',
             '\n',

             # cfn-signal
             '/opt/aws/bin/cfn-signal -e $? ',
             ' --stack ', Ref('AWS::StackName'),
             ' --resource DevServer',
             ' --region ', Ref('AWS::Region'),
             '\n'
             ])
    ),
    Tags=Tags(
        StackName=Ref('AWS::StackName'),
        Name='dev-server',
    )
)
)

# outputs
template.add_output([
    Output('AllSSHsg',
           Description='Security group to enable SSH from everywhere',
           Value=Ref(all_ssh)),
    Output('DevSubnet',
           Description='Public Subnet used for Dev Servers',
           Value=Ref(dev_public_subnet)),

    Output('DevServer',
           Description='EC2 Instance',
           Value=Ref(ec2_instance))
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'DevServer'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
