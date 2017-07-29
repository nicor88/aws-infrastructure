import boto3
import datetime as dt
import hashlib

logs = boto3.client('logs')

app_name = 'app_test'
logGroupName = 'test'

logStreamName = '{}-{}'.format(dt.datetime.now().strftime('%Y/%m/%d-%H.%M'), app_name)

try:
    logs.create_log_group(logGroupName=logGroupName)
except Exception as err:
    print(err)
# create a log stream
try:
    logs.create_log_stream(logGroupName=logGroupName, logStreamName=logStreamName)
except Exception as err:
    logs.create_log_stream(logGroupName=logGroupName, logStreamName=logStreamName)
log = {'timestamp': int(dt.datetime.now().strftime("%s")) * 1000 , 'message': 'just a test'}
logs.put_log_events(logGroupName=logGroupName,
                    logStreamName=logStreamName,
                    logEvents=[log])
