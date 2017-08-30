from __future__ import print_function
from pyspark.sql import SparkSession
from pyspark.streaming import StreamingContext
from pyspark import StorageLevel
from pyspark.streaming.kinesis import KinesisUtils, InitialPositionInStream
import json


spark = SparkSession.builder.appName('test').getOrCreate()
sc = spark.sparkContext
streaming_ctx = StreamingContext(sc, 10)


def printRecord(rdd):
    print("========================================================")
    print("Starting new RDD")
    print("========================================================")
    # rdd.foreach(lambda record: print(record.encode('utf8')))
    print('---------> Cound of RDD {}'.format(rdd.count()))
    # TODO to save use append mode
    # rdd.saveAsTextFile('s3://nicor-data/test-streaming/')

app_name = 'TestStreaming'
stream_name = 'DevStreamS3'
region_name = 'eu-west-1'
endpoint_url = 'https://kinesis.eu-west-1.amazonaws.com'

dstream = KinesisUtils.createStream(streaming_ctx,
                                    app_name, stream_name,
                                    endpoint_url,
                                    region_name,
                                    InitialPositionInStream.LATEST,
                                    10,
                                    StorageLevel.MEMORY_AND_DISK_2)
dstream.foreachRDD(printRecord)
streaming_ctx.start()
streaming_ctx.awaitTermination()

# examples
# spark-submit --deploy-mode client --packages org.apache.spark:spark-streaming-kinesis-asl_2.11:2.2.0 --master yarn steps/streaming.py
# https://github.com/MayankAyush/KinesisSparkIntegration/blob/41707745c477b8e39c724b7ffd167bd4ff690885/pysparkKinesisIntegration.py
# https://github.com/apache/spark/blob/master/external/kinesis-asl/src/main/python/examples/streaming/kinesis_wordcount_asl.py

# submit job example
# spark-submit --deploy-mode client --packages org.apache.spark:spark-streaming-kinesis-asl_2.11:2.2.0 --master local[4] steps/streaming.py
# spark-submit --deploy-mode client --packages org.apache.spark:spark-streaming-kinesis-asl_2.11:2.2.0 --master yarn --num-executors 1 steps/streaming.py

## Some learnings
# use a number of executors multiple of the number of shards
# one executor for core at least