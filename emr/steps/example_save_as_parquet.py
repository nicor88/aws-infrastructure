"""
# how to call in the master node of the cluster
# spark-submit --deploy-mode client --master yarn example_save_as_parquet.py
"""

import boto3
import datetime as dt
import hashlib
import logging
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# init spark
spark = SparkSession.builder.appName('JsonToParquet').getOrCreate()
sc = spark.sparkContext
sqlContext = SQLContext(sc)

# read
df = sqlContext.read.json('s3://nicor-data/samples/world_bank.json')

# TODO send events to cloudwatch

# save df as parquet
now_str = str(dt.datetime.now())
now_hash = hashlib.md5(now_str.encode('utf-8')).hexdigest()
bucket_name = 'nicor-data'
base_bucket = 's3://{}'.format(bucket_name)

destination_path = '{}/parquet/test-write-{}'.format(base_bucket, now_hash)
# df.repartition(2).write.parquet(destination_path)
df.write.parquet(destination_path)

spark.stop()
