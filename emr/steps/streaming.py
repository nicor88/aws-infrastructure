"""
Sample spark job to process events from a Kinesis Stream

# Example 1: submit the spark job using only the master with 4 cores
spark-submit --deploy-mode client --packages org.apache.spark:spark-streaming-kinesis-asl_2.11:2.2.0 --master local[4] steps/streaming.py

# Example 2: submit the spark job using yarn with specified amount of executors
spark-submit --deploy-mode client --packages org.apache.spark:spark-streaming-kinesis-asl_2.11:2.2.0 --master yarn --num-executors 4 steps/streaming.py

# Notes
- Use a number of executors multiple of the number of shards (one executor for core at least)
- It looks that the app need to be initialize first with

# References
https://github.com/MayankAyush/KinesisSparkIntegration/blob/41707745c477b8e39c724b7ffd167bd4ff690885/pysparkKinesisIntegration.py
https://github.com/apache/spark/blob/master/external/kinesis-asl/src/main/python/examples/streaming/kinesis_wordcount_asl.py

"""
import datetime as dt
import json
import uuid

from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from pyspark.streaming import StreamingContext
from pyspark import StorageLevel
from pyspark.streaming.kinesis import KinesisUtils, InitialPositionInStream

app_name = 'test_spark_streaming'
kinesis_stream_name = 'DevStream'
region_name = 'eu-west-1'
kinesis_endpoint_url = 'https://kinesis.eu-west-1.amazonaws.com'
windows_size_secs = 10

spark = SparkSession.builder.appName(app_name).getOrCreate()
sc = spark.sparkContext
sql_ctx = SQLContext(sc)
streaming_ctx = StreamingContext(sc, windows_size_secs)


def process_event(event):
    json_event = json.loads(event)
    # the event is print only if the app is running in master mode local
    print(json_event)
    return json_event


def build_path(*, lang):
    base_path = 's3://nicor-data/twitter'
    formatted_date = dt.datetime.now().strftime('%Y/%m/%d/%H')
    batch_id = str(uuid.uuid4())
    final_path = '{base_path}/{lang}/{date}/{batch_id}/'.format(base_path=base_path,
                                                                lang=lang,
                                                                date=formatted_date,
                                                                batch_id=batch_id)
    return final_path


def handle_rdd(rdd):
    print("---------> Processing new RDD")
    rdd_count = rdd.count()
    print('---------> Count of Initial RDD {}'.format(rdd_count))
    if rdd_count > 0:
        lang = 'en'
        rdd_transformed = rdd.map(lambda e: process_event(e))
        print('---------> Count of Transformed RDD {}'.format(rdd_transformed.count()))
        rdd_filtered = rdd_transformed.filter(lambda e: e['lang'] == lang)
        # just a simple example to filter the RDD
        print('---------> Count of Filtered RDD {}'.format(rdd_filtered.count()))
        rdd.saveAsTextFile(build_path(lang=lang))


dstream = KinesisUtils.createStream(streaming_ctx,
                                    app_name, kinesis_stream_name,
                                    kinesis_endpoint_url,
                                    region_name,
                                    InitialPositionInStream.LATEST,
                                    windows_size_secs,
                                    StorageLevel.MEMORY_AND_DISK_2)
dstream.foreachRDD(handle_rdd)
streaming_ctx.start()
streaming_ctx.awaitTermination()

# streaming_ctx.stop()
