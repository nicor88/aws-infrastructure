import os
import boto3
import datetime as dt
import json

import logging
logger = logging.getLogger(__name__)

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_PROFILE"] = "nicor88-aws-dev"

kinesis = boto3.client('kinesis')
firehose = boto3.client('firehose')

# put a single record to the stream
record_1 = {
    'created_at': dt.datetime.now().isoformat(),
    'name': 'user:created',
    'country_code3': 'ITA'
}
kinesis.put_record(StreamName='test_stream', Data=json.dumps(record_1), PartitionKey='created_at')


# put multiple records in the stream

record_2 = {
    'created_at': dt.datetime.now().isoformat(),
    'name': 'user:created',
    'country_code3': 'DEU'
}


def prepare_kinesis_records(*, records, partition_key):
    kinesis_records = []

    for r in records:
        record = {
            'PartitionKey': partition_key,
            'Data': json.dumps(r)
        }
        kinesis_records.append(record)
    return kinesis_records

records = [record_1, record_2]

k_records = prepare_kinesis_records(records=records, partition_key='created_at')

logger.info('Putting multiple {} records'.format(len(records)))
r = kinesis.put_records(StreamName='test_stream', Records=k_records)

# read records from a specific timestamp
stream = kinesis.describe_stream(StreamName='test_stream')
iterator = kinesis.get_shard_iterator(
    StreamName='test_stream',
    ShardId=stream['StreamDescription']['Shards'][0]['ShardId'],
    ShardIteratorType='TRIM_HORIZON'

)
records_from_the_stream = kinesis.get_records(ShardIterator=iterator['ShardIterator'],
                                              Limit=100)['Records']
logger.info('{} records in the stream'.format(len(records_from_the_stream)))

# put records in batch from kinesis to firehose
records_for_firehose = [{'Data': r['Data']} for r in records_from_the_stream]

firehose.put_record_batch(
    DeliveryStreamName='test_delivery_stream',
    Records=records_for_firehose
)
