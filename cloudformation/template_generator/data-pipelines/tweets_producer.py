import boto3
from pkg_resources import resource_string

from awacs.aws import Statement, Allow, Policy, Action
import awacs.s3 as s3
import ruamel_yaml as yaml
from troposphere import ec2
from troposphere import iam
from troposphere import Base64, GetAtt, Join, Output, Parameter, Ref, Tags, Template

from troposphere.cloudformation import Init, InitFile, InitFiles, InitConfig, InitService, \
    InitServices
from troposphere.autoscaling import Metadata
from troposphere.codedeploy import Application, DeploymentGroup, Ec2TagFilters

import cloudformation.utils as utils

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'twitter_producer_config.yml'))
networking_resources = utils.get_stack_resources(stack_name=cfg['networking_stack_name'])

STACK_NAME = cfg['ec2']['stack_name']
SERVER_NAME = 'TwitterProducer'

template = Template()
description = 'Twitter Producer Stack'
template.add_description(description)
template.add_version('2010-09-09')

# instance role
instance_policy_doc = Policy(
    Statement=[
        Statement(
            Sid='KinesisAccess',
            Effect=Allow,
            Action=[Action('kinesis', '*')
                    ],
            Resource=[
                'arn:aws:kinesis:eu-west-1:749785218022:stream/DevStreamES']
        ),
        Statement(
            Sid='LogsAccess',
            Effect=Allow,
            Action=[Action('logs', '*')
                    ],
            Resource=[
                '*'
            ]
        ),
        Statement(
            Sid='ReadS3DeploymentBucket',
            Effect=Allow,
            Action=[Action('s3', 'Get*'),
                    Action('s3', 'List*')
                    ],
            Resource=[
                s3.ARN('nicor-dev'),
                s3.ARN('nicor-dev/*'),
            ]
        )
    ]
)

instance_role = template.add_resource(
    iam.Role(
        "InstanceRole",
        RoleName='TweetProducerRole',
        AssumeRolePolicyDocument={
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": [
                        "ec2.amazonaws.com"
                    ]
                },
                "Action": ["sts:AssumeRole"]
            }]
        },

        Policies=[
            iam.Policy(
                PolicyName='{}InstancePolicy'.format(STACK_NAME),
                PolicyDocument=instance_policy_doc,
            ),
        ]
    ))

instance_profile = template.add_resource(
    iam.InstanceProfile(
        "InstanceProfile",
        Roles=[Ref(instance_role)],
        InstanceProfileName='TweeterUploaderInstanceProfile'
    ))

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
            '/root/.bashrc': InitFile(
                content=Join('', [
                    'export PATH="/home/ec2-user/miniconda/bin:$PATH"\n'
                    'export TWITTER_KEYWORDS="Sardegna,Python"\n'
                    'export ENV="production"\n'
                ]),
                owner='root',
                mode='000400',
                group='root'),
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
                              f'path=Resources.{SERVER_NAME}.Metadata.AWS::CloudFormation::Init\n',
                              'action=/opt/aws/bin/cfn-init -v',
                              ' --stack ', Ref('AWS::StackId'),
                              f' --resource {SERVER_NAME}',
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

# ec2 instance
ec2_instance = template.add_resource(ec2.Instance(
    f'{SERVER_NAME}',
    InstanceType=cfg['ec2']['instance_type'],
    IamInstanceProfile=Ref(instance_profile),
    ImageId=cfg['ec2']['ami_version'],
    SubnetId=networking_resources['GenericEC2Subnet'],
    SecurityGroupIds=[networking_resources['AllSshSecurityGroup']],
    InstanceInitiatedShutdownBehavior='stop',
    Monitoring=True,
    KeyName='nicor88-dev',
    Metadata=instance_metadata,
    BlockDeviceMappings=[{
        'DeviceName': '/dev/xvda',  # "/dev/sda1" if the ami is ubuntu
        'Ebs': {
            'VolumeType': 'gp2',
            'DeleteOnTermination': 'true',
            'VolumeSize': '10'
        }
    }],
    UserData=Base64(
        Join(
            '',
            ['#!/bin/bash -xe\n',

             'yum install -y gcc\n',

             # cfn-init: install what is specified in the metadata section
             '/opt/aws/bin/cfn-init -v ',
             ' --stack ', Ref('AWS::StackName'),
             f' --resource {SERVER_NAME}',
             ' --region ', Ref('AWS::Region'), '\n',

             # cfn-hup
             # Start up the cfn-hup daemon to listen for changes to the server metadata
             'yum install -y aws-cfn-bootstrap\n',
             '/opt/aws/bin/cfn-hup || error_exit "Failed to start cfn-hup"',
             '\n',

             # cfn-signal
             '/opt/aws/bin/cfn-signal -e $? ',
             ' --stack ', Ref('AWS::StackName'),
             f' --resource {SERVER_NAME}',
             ' --region ', Ref('AWS::Region'),
             '\n'
             ])
    ),
    Tags=Tags(
        StackName=Ref('AWS::StackName'),
        Name='twitter-producer',
    )
)
)

code_deploy_service_role = template.add_resource(
    iam.Role(
        "CodeDeployServiceRole",
        AssumeRolePolicyDocument={
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": [
                        "codedeploy.amazonaws.com"
                    ]
                },
                "Action": ["sts:AssumeRole"]
            }]
        },
        Policies=[
            iam.Policy(
                PolicyName='{}CodeDeployPolicy'.format(STACK_NAME),
                PolicyDocument=Policy(
                    Statement=[
                        Statement(
                            Sid='EC2Access',
                            Effect=Allow,
                            Action=[Action('ec2', '*')
                                    ],
                            Resource=[
                                '*',
                            ]
                        ),
                    ]
                ),
            ),
        ]
    ))

# Code Deploy Setup
code_deploy_application = template.add_resource(
    Application('TwitterProducerCodeDeployApplication',
                ApplicationName='TwitterProducer'
                )
)

deployment_group = template.add_resource(
    DeploymentGroup(
        'DeploymentGroup',
        ApplicationName=Ref(code_deploy_application),
        Ec2TagFilters=[
            Ec2TagFilters('TwitterProducerEc2Filter',
                          Type='KEY_AND_VALUE',
                          Key='Name',
                          Value='twitter-producer'
                          )],
        DeploymentGroupName='TwitterProducer',
        ServiceRoleArn=GetAtt(code_deploy_service_role, 'Arn'),
        DeploymentConfigName='CodeDeployDefault.HalfAtATime',
    )
)

# outputs
template.add_output([
    Output('TwitterProducer',
           Description='EC2 Instance',
           Value=Ref(ec2_instance)),
    Output('TwitterProducerPublicDnsName',
           Description='PublicIP of EC2 Instance',
           Value=GetAtt(ec2_instance, 'PublicDnsName'))
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Capabilities': [
        'CAPABILITY_IAM',
        'CAPABILITY_NAMED_IAM'
    ],
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'TwitterProducer'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)

# code deploy path
# s3://nicor-dev/deployments/apps/twitter-to-kinesis/2296c9aa26db8ee6225beceaab474c7968a9c68c.zip