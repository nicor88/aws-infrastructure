import os
import boto3
import logging
import datetime as dt
import json
logger = logging.getLogger(__name__)

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_PROFILE"] = "nicor88-aws-dev"

firehose = boto3.client('firehose')

record = {'name': 'test', 'created_at': dt.datetime.now().isoformat()}


firehose.put_record(DeliveryStreamName='DevDeliveryStreamES',
                    Record={'Data':json.dumps(record)}

)
