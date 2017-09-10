import boto3
import os

from troposphere.rds import DBInstance, DBSubnetGroup
from troposphere import GetAtt, Join, Output, Parameter, Ref, Tags, Template
from troposphere.constants import SUBNET_ID

import cloudformation.utils as utils

networking_resources = utils.get_stack_resources(stack_name='NetworkingStack')

STACK_NAME = 'Storage-RDS-Postgres-Stack'

template = Template()
description = 'Storage Stack containing a RDS Postgres Instance'
template.add_description(description)
template.add_version('2010-09-09')

master_user = template.add_parameter(
    Parameter(
        'MasterUser',
        Type='String',
        Description='Master User for Postgres Instance',
    )
)

master_user_password = template.add_parameter(
    Parameter(
        'MasterUserPassword',
        Type='String',
        Description=' Master User Password for Postgres Instance',
    )
)

subnet_az_1 = template.add_parameter(
    Parameter(
        'SubnetAZ1',
        Type=SUBNET_ID,
        Description='Subnet in AZ 1 to use for Postgres Instance',
    )
)
subnet_az_2 = template.add_parameter(
    Parameter(
        'SubnetAZ2',
        Type=SUBNET_ID,
        Description='Subnet in AZ 2 to use for Postgres Instance',
    )
)

security_group = template.add_parameter(
    Parameter(
        'SecurityGroup',
        Type='String',
        Description='Security Group to use for Postgres',
    )
)

subnet_group = template.add_resource(
    DBSubnetGroup('SubnetGroup',
                  DBSubnetGroupDescription='Subnets group for Postgres Instance',
                  SubnetIds=[Ref(subnet_az_1), Ref(subnet_az_2)])
)

rds_postgres = template.add_resource(DBInstance(
    'DB',
    DBInstanceIdentifier='dev-db',
    DBName='dev',
    DBInstanceClass='db.t2.micro',
    AllocatedStorage='10',
    Engine='postgres',
    EngineVersion='9.6.3',
    MasterUsername=Ref(master_user),
    MasterUserPassword=Ref(master_user_password),
    DBSubnetGroupName=Ref(subnet_group),
    VPCSecurityGroups=[Ref(security_group)],
    PubliclyAccessible=True
))

# Outputs
template.add_output([
    Output('RDSPostgres',
           Description='RDS Postgres Instance',
           Value=Ref(rds_postgres)),
    Output('RDSPostgresEndpointAddress',
           Description='RDS Postgres Instance',
           Value=GetAtt(rds_postgres, 'Endpoint.Address')),
    Output('RDSPostgresEndpointPort',
           Description='RDS Postgres Instance',
           Value=GetAtt(rds_postgres, 'Endpoint.Port')),
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Parameters': [
        {
            'ParameterKey': 'SubnetAZ1',
            'ParameterValue': networking_resources['GenericPublicSubnetEuWest1b'],
        },
        {
            'ParameterKey': 'SubnetAZ2',
            'ParameterValue': networking_resources['GenericPublicSubnetEuWest1c'],
        },
        {
            'ParameterKey': 'SecurityGroup',
            'ParameterValue': networking_resources['PostgresSecurityGroup'],
        },
        {
            'ParameterKey': 'MasterUser',
            'ParameterValue': 'nicor88',
        },
        {
            'ParameterKey': 'MasterUserPassword',
            'ParameterValue': os.environ['REDSHIFT_MASTER_PASSWORD'],
        },
    ],
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'BoilerplateTemplate'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
# utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
