import json
import datetime as dt


def create_kinesis_record(*, producer, name):
    record = {}
    record['meta.created_at'] = dt.datetime.now().isoformat()
    record['meta.producer'] = producer
    record['name'] = name
    return record

def prepare_kinesis_records(*, records, partition_key):
    kinesis_records = []

    for r in records:
        record = {
            'PartitionKey': partition_key,
            'Data': json.dumps(r)
        }
        kinesis_records.append(record)
    return kinesis_records
