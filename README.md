# aws-dev
Collection of examples in AWS

## Profiles with Boto3
To manage different profiles create a file __~/.aws/credentials__ with this content:

<pre>[default]
aws_access_key_id=foo
aws_secret_access_key=bar

[nicor88-aws-dev]
aws_access_key_id=foo2
aws_secret_access_key=bar2
</pre>

To select the spefic profile in boto use:
<pre>session = boto3.Session(profile_name='nicor88-aws-dev')
s3_client = session.client('s3')
</pre>

## AWS Conda Environment
Install Anaconda o Miniconda
<pre>conda env create -f environment.yml
source activate aws-dev
</pre>

After installing a new package in the environment, update the env file running:
<pre>conda env export > environment.yml
</pre>
