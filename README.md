# aws-infrastructure
Collection of resources to manage AWS infrastructure

## Requirements
* Python >= 3.4
* Install requirements: `pip install -r requirements.txt`

## AWS Profiles
To manage different profiles create a file __~/.aws/credentials__ with this content:

<pre>[default]
aws_access_key_id=foo
aws_secret_access_key=bar

[nicor88]
aws_access_key_id=foo2
aws_secret_access_key=bar2
</pre>

In setup this env variables, to work with a specific profile:
<pre>import os
os.environ["AWS_PROFILE"] = "nicor88"
os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
</pre>
