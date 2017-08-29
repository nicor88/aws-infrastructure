from pyspark.streaming import StreamingContext
from pyspark.streaming.kinesis import KinesisUtils, InitialPositionInStream

spark = SparkSession.builder.master("yarn-client").getOrCreate()
sc = spark.sparkContext
sqlContext = SQLContext(sc)

streaming_ctx = StreamingContext(sc, 10)

def printRecord(rdd):
    print("========================================================")
    print("Starting new RDD")
    print("========================================================")
    rdd.foreach(lambda record: print(record.encode('utf8')))

app_name = 'TestStreaming'
stream_name = 'DevStreamS3'
region_name = 'eu-west-1'
endpoint_url = 'https://kinesis.eu-west-1.amazonaws.com'

dstream = KinesisUtils.createStream(
        streaming_ctx, app_name, stream_name, endpoint_url, region_name, InitialPositionInStream.TRIM_HORIZON, 10)
dstream.foreachRDD(printRecord)
streaming_ctx.start()
streaming_ctx.awaitTermination()
