import os
import boto3
from pkg_resources import resource_string
import ruamel_yaml as yaml

from troposphere import s3
from troposphere import Output, Ref, Template

# load config
cfg = yaml.load(resource_string('cloudformation.config', 'dev_config.yml'))

# setup aws session
os.environ['AWS_DEFAULT_REGION'] = cfg['region']
os.environ['AWS_PROFILE'] = 'nicor88-aws-dev'
cfn = boto3.client('cloudformation')

STACK_NAME = cfg['s3']['stack_name']

template = Template()
description = 'S3 Bucket mostly used for development reasons'
template.add_description(description)
# AWSTemplateFormatVersion
template.add_version('2010-09-09')

s3_dev_bucket = template.add_resource(
    s3.Bucket('S3DevBucket',
              BucketName='nicor-dev'
              )
)

s3_data_bucket = template.add_resource(
    s3.Bucket('S3DataBucket',
              BucketName='nicor-data'
              )
)

# stack outputs
template.add_output([
    Output('S3DevBucket',
           Description='S3 bucket for development',
           Value=Ref(s3_dev_bucket))])

template.add_output([
    Output('S3DataBucket',
           Description='S3 bucket to put data',
           Value=Ref(s3_data_bucket))])


template_json = template.to_json(indent=4)
print(template_json)

stack_args = {
    'StackName': STACK_NAME,
    'TemplateBody': template_json,
    'Tags': [
        {
            'Key': 'Purpose',
            'Value': 'DevS3Buckets'
        }
    ]
}

cfn.validate_template(TemplateBody=template_json)

# cfn.create_stack(**stack_args)
# cfn.update_stack(**stack_args)
# cfn.delete_stack(StackName=STACK_NAME)
