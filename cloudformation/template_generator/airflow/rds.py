import boto3

from troposphere import ec2
from troposphere.rds import DBInstance, DBSubnetGroup
from troposphere import GetAtt, Output, Parameter, Ref, Tags, Template

import cloudformation.utils as utils

STACK_NAME = 'airflow-rds'

template = Template()
description = 'Stack containing an RDS Postgres Instance for Airflow'
template.add_description(description)
template.add_version('2010-09-09')

vpc_id = template.add_parameter(
    Parameter(
        'VpcId',
        Type='String',
        Default='vpc-8b708fec',
        Description='VPC ID',
    )
)

private_route_table = template.add_parameter(
    Parameter(
        'PrivateRouteTable',
        Type='String',
        Default='rtb-964c7ef0',
        Description='Routing Table used for Private subnets',
    )
)

db_name = template.add_parameter(
    Parameter(
        'DBName',
        Type='String',
        Default='airflow',
        Description='Name of the Database used for Metadata storage by Airflow',
    )
)

master_user = template.add_parameter(
    Parameter(
        'MasterUser',
        Type='String',
        Default='airflow',
        Description='Master User for Postgres Instance',
    )
)

master_user_password = template.add_parameter(
    Parameter(
        'MasterUserPassword',
        Type='String',
        Default='airflow_dev',
        Description=' Master User Password for Postgres Instance',
    )
)

# Networking
airflow_rds_private_subnet_eu_west_1a = template.add_resource(
    ec2.Subnet(
        'AirflowRDSPrivateSubnetEuWest1a',
        AvailabilityZone='eu-west-1a',
        CidrBlock='172.31.20.0/24',
        VpcId=Ref(vpc_id),
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            AZ='eu-west-1b',
            Name='airflow-rds-private-eu-west-1a'
        )
    )
)

airflow_rds_private_subnet_eu_west_1a_route_table_association = template.add_resource(
    ec2.SubnetRouteTableAssociation('AirflowRDSPrivateSubnetEuWest1aRouteTableAssociation',
                                    RouteTableId=Ref(private_route_table),
                                    SubnetId=Ref(airflow_rds_private_subnet_eu_west_1a)
                                    )
)

airflow_rds_private_subnet_eu_west_1b = template.add_resource(
    ec2.Subnet(
        'AirflowRDSPrivateSubnetEuWest1b',
        AvailabilityZone='eu-west-1b',
        CidrBlock='172.31.21.0/24',
        VpcId=Ref(vpc_id),
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            AZ='eu-west-1b',
            Name='airflow-rds-private-eu-west-1b'
        )
    )
)

airflow_rds_private_subnet_eu_west_1b_route_table_association = template.add_resource(
    ec2.SubnetRouteTableAssociation('AirflowRDSPrivateSubnetEuWest1bRouteTableAssociation',
                                    RouteTableId=Ref(private_route_table),
                                    SubnetId=Ref(airflow_rds_private_subnet_eu_west_1b)
                                    )
)

subnet_group = template.add_resource(
    DBSubnetGroup('SubnetGroup',
                  DBSubnetGroupDescription='Subnets group for Postgres Instance',
                  SubnetIds=[Ref(airflow_rds_private_subnet_eu_west_1a), Ref(airflow_rds_private_subnet_eu_west_1b)])
)

security_group = template.add_resource(
    ec2.SecurityGroup(
        'AirflowRdsSg',
        VpcId=Ref(vpc_id),
        GroupDescription='Allow Postgress Traffic inside VPC',
        SecurityGroupIngress=[
            # allow access only inside the VPC
            ec2.SecurityGroupRule(
                IpProtocol='tcp',
                FromPort='5432',
                ToPort='5432',
                CidrIp='172.31.0.0/16'
            )
        ],
        Tags=Tags(
            StackName=Ref('AWS::StackName'),
            Name='airflow-rds-sg'
        )
    )
)

airflow_rds_postgres = template.add_resource(DBInstance(
    'AirflowRDS',
    DBInstanceIdentifier='airflow',
    DBName=Ref(db_name),
    DBInstanceClass='db.t2.micro',
    AllocatedStorage='10',
    Engine='postgres',
    EngineVersion='9.6.3',
    MasterUsername=Ref(master_user),
    MasterUserPassword=Ref(master_user_password),
    DBSubnetGroupName=Ref(subnet_group),
    VPCSecurityGroups=[Ref(security_group)]
))

# Outputs
template.add_output([
    Output('RDSPostgresInstance',
           Description='RDS Postgres Instance',
           Value=Ref(airflow_rds_postgres)),
    Output('RDSPostgresDBName',
           Description='RDS Postgres DB name',
           Value=Ref(db_name)),
    Output('RDSPostgresEndpointAddress',
           Description='RDS Postgres Instance',
           Value=GetAtt(airflow_rds_postgres, 'Endpoint.Address')),
    Output('RDSPostgresEndpointPort',
           Description='RDS Postgres Instance',
           Value=GetAtt(airflow_rds_postgres, 'Endpoint.Port')),
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
