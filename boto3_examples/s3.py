import boto3
import os

os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_PROFILE"] = "nicor88-aws-dev"

s3 = boto3.client('s3')

# using sessions
# session = boto3.Session(profile_name='nicor88-aws-dev')
# s3 = session.client('s3')

# get all the buckets
buckets = s3.list_buckets()

# retrieve buckets names
buckets_names = [p['Name'] for p in s3.list_buckets()['Buckets']]

# retrieve bucket content
objs = s3.list_objects_v2(Bucket=buckets[0])['Contents']
objs_keys = [o['Key'] for o in objs]

# retrieve content of a bucket inside a folder
bucket_name = 'nicor-data-samples'
folder = 'samples/'
objs_folder = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder, Delimiter='/')
objs_folder_content = [o['Key'] for o in objs_folder['Contents'] if o['Key'] != folder]
