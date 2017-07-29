"""
# how to call in the master node of the cluster
# spark-submit --deploy-mode client --master yarn example_save_as_parquet.py
"""

import boto3
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
df.repartion('1').write.parquet('s3://nicor-data/test-write/')

spark.stop()
