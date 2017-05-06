# aws-dev
Collection of examples in AWS

## AWS Conda Environment
Install Anaconda o Miniconda
<pre>conda env create -f conda-env-dev.yml
source activate aws-dev
</pre>
The env contain also **aws cli**

After installing a new package update the env file:
<pre>conda env export > conda-env-dev.yml
</pre>

## AWS Profiles
To manage different profiles create a file __~/.aws/credentials__ with this content:

<pre>[default]
aws_access_key_id=foo
aws_secret_access_key=bar

[nicor88-aws-dev]
aws_access_key_id=foo2
aws_secret_access_key=bar2
</pre>

### Handle profiles in boto3
To use a specific profile in boto3 use:
<pre>session = boto3.Session(profile_name='nicor88-aws-dev')
s3_client = session.client('s3')
</pre>

