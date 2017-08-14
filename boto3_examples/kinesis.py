import os
import boto3
from botocore.client import Config
import json
import logging
import boto3_examples.utils as u
from pkg_resources import resource_string
import ruamel_yaml as yaml

# setup
logger = logging.getLogger(__name__)
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_PROFILE"] = "nicor88-aws-dev"

# configure client using bot3

# if you are using a lambda function to put data into a kinesis stream be sure that the timeout
# of boto3 client is < that the timeout of the lambda function
kinesis = boto3.client('kinesis', config=Config(connect_timeout=1000))
# https://github.com/boto/botocore/pull/891


# put a single record to the stream
def put_one_record_to_kinesis(*, stream_name):
    res = kinesis.put_record(StreamName=stream_name,
                             Data=json.dumps(
                                 u.create_kinesis_record(producer='python_script',
                                                         name='test:insert:one_record')),
                             PartitionKey='created_at')
    logger.info(res)
    return res


# put multiple records in the stream
def put_many_records_to_kinesis(*, stream_name, records_number):
    records = []
    for i in range(records_number):
        record = u.create_kinesis_record(producer='python_script',
                                 name='test:insert:many_record')
        records.append(record)
    k_records = u.prepare_kinesis_records(records=records, partition_key='created_at')
    logger.info('Putting multiple {} records'.format(len(k_records)))
    res = kinesis.put_records(StreamName=stream_name, Records=k_records)
    logger.info(res)
    return res


# read records from the stream with TRIM_HORIZON
def read_records_from_kinesis(*, stream_name):
    stream = kinesis.describe_stream(StreamName=stream_name)
    iterator = kinesis.get_shard_iterator(
        StreamName='test_stream',
        ShardId=stream['StreamDescription']['Shards'][0]['ShardId'],
        ShardIteratorType='LATEST'
    )
    records_from_the_stream = kinesis.get_records(ShardIterator=iterator['ShardIterator'],
                                                  Limit=200)['Records']
    logger.info('{} records in the stream'.format(len(records_from_the_stream)))

    return records_from_the_stream

# Examples
# put_one_record_to_kinesis(stream_name='DevStream')
# put_many_records_to_kinesis(stream_name='DevStream', records_number=50)
# read_records_from_kinesis(stream_name='DevStream')
