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
region = us-east-1

[your_other_profile]
aws_access_key_id=foo2
aws_secret_access_key=bar2
region = us-east-1
</pre>

To point to the right profile use ENV variables
<pre>
export AWS_PROFILE=your_other_profile
# this will overwrite the region in the profile configuration
export AWS_DEFAULT_REGION=eu-west-1
</pre>
