import os
import boto3
import json
import logging
import boto3_examples.utils as u

# setup
logger = logging.getLogger(__name__)
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_PROFILE"] = "nicor88-aws-dev"

# configure client using bot3
kinesis = boto3.client('kinesis')


# put a single record to the stream
def put_one_record_to_kinesis():
    res = kinesis.put_record(StreamName='test_stream',
                             Data=json.dumps(
                                 u.create_kinesis_record(producer='python_script',
                                                         name='test:insert:one_record')),
                             PartitionKey='created_at')
    logger.info(res)
    return res


# put multiple records in the stream
def put_many_records_to_kinesis(records_number):
    records = []
    for i in range(records_number):
        record = u.create_kinesis_record(producer='python_script',
                                 name='test:insert:many_record')
        records.append(record)
    k_records = u.prepare_kinesis_records(records=records, partition_key='created_at')
    logger.info('Putting multiple {} records'.format(len(k_records)))
    res = kinesis.put_records(StreamName='test_stream', Records=k_records)
    logger.info(res)
    return res


# read records from the stream with TRIM_HORIZON
def read_records_from_kinesis():
    stream = kinesis.describe_stream(StreamName='test_stream')
    iterator = kinesis.get_shard_iterator(
        StreamName='test_stream',
        ShardId=stream['StreamDescription']['Shards'][0]['ShardId'],
        ShardIteratorType='TRIM_HORIZON'
    )
    records_from_the_stream = kinesis.get_records(ShardIterator=iterator['ShardIterator'],
                                                  Limit=200)['Records']
    logger.info('{} records in the stream'.format(len(records_from_the_stream)))

    return records_from_the_stream

# put_one_record_to_kinesis()
# put_many_records_to_kinesis(5)
# read_records_from_kinesis()
