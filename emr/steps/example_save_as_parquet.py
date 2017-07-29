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

# save df as parquet
df.repartion('1').write.parquet('s3://nicor-data/test-write/')

spark.stop()
