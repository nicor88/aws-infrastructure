import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere.elasticsearch import Domain, ElasticsearchClusterConfig, EBSOptions
from troposphere.elasticsearch import SnapshotOptions
from awacs.aws import Action, Allow, Condition, Policy, Statement
from awacs.aws import IpAddress, StringEquals
from troposphere import GetAtt, Join, Output, Parameter, Ref, Tags, Template

import cloudformation.utils as utils

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'boilerplate_config.yml'))

STACK_NAME = 'Storage-Elastichsearch-Stack'

template = Template()
description = 'Storage Stack containing a Elastic Search'
template.add_description(description)
template.add_version('2010-09-09')

access_policy = Policy(
    Statement=[
        Statement(
            Sid='FullAccess',
            Effect=Allow,
            Action=[Action('es', '*'),
                    ],
            Resource=[
                '*'
            ],
            # Condition=Condition(
            #     IpAddress({
            #         'aws:SourceIp': '...../24'
            #     }),
            # )
        ),
    ]
)

elasticsearch_domain = template.add_resource(
    Domain('ElasticsearchDomain',
           DomainName='nicor88-dev',
           AccessPolicies=access_policy,
           ElasticsearchVersion='5.3',
           ElasticsearchClusterConfig=ElasticsearchClusterConfig(
               InstanceCount=1,
               InstanceType='t2.small.elasticsearch',
               ZoneAwarenessEnabled=False,
           ),
           EBSOptions=EBSOptions(EBSEnabled=True,
                                 VolumeSize='10',
                                 VolumeType='gp2'  # General Purpose SSD
                                 ),
           SnapshotOptions=SnapshotOptions(AutomatedSnapshotStartHour=0),
           Tags=Tags(
               Name='nicor88-dev'
           )
           )
)

# Outputs
template.add_output([
    Output('ElasticsearchDomain',
           Description='Elasticsearch Domain',
           Value=Ref(elasticsearch_domain)),
    Output('ElasticsearchDomainEndpoint',
           Description='ElasticsearchDomainEndpoint',
           Value=GetAtt(elasticsearch_domain, 'DomainEndpoint')
           ),
])

template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'Elasticsearch'
        }
    ]
}

cfn = boto3.client('cloudformation')
cfn.validate_template(TemplateBody=template_json)
# utils.write_template(**stack_args)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
