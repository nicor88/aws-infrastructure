[![Build Status](https://travis-ci.org/nicor88/aws-infrastructure.svg?branch=master)](https://travis-ci.org/nicor88/aws-infrastructure)

# aws-infrastructure
Collection of resources to manage AWS infrastructure

## AWS Conda Environment
Install Anaconda o Miniconda
<pre>conda env create -f conda-env.yml
source activate aws-infrastructure
</pre>
The env contain also **aws cli**

After installing a new package update the env file:
<pre>conda env export -n aws-infrastructure > conda-env.yml
</pre>

## AWS Profiles
To manage different profiles create a file __~/.aws/credentials__ with this content:

<pre>[default]
aws_access_key_id=foo
aws_secret_access_key=bar

[nicor88-aws]
aws_access_key_id=foo2
aws_secret_access_key=bar2
</pre>

### Handle profiles in boto3
To use a specific profile in boto3 use:
<pre>session = boto3.Session(profile_name='nicor88-aws')
s3_client = session.client('s3')
</pre>

