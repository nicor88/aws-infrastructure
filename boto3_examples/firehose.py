import os
import boto3
import logging
logger = logging.getLogger(__name__)

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_PROFILE"] = "nicor88-aws-dev"

kinesis = boto3.client('kinesis')
firehose = boto3.client('firehose')

# read records with TRIM_HORIZON
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