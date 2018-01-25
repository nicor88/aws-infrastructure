<pre>aws ecr get-login --no-include-email --region eu-west-1 --profile nicor88
# run the login command return by the command above
docker build --rm=True -t conda .

docker tag conda:latest 749785218022.dkr.ecr.eu-west-1.amazonaws.com/conda:latest
docker push 749785218022.dkr.ecr.eu-west-1.amazonaws.com/conda:latest
</pre>