#!/usr/bin/env bash

source activate aws-dev
export PYTHONPATH=/Users/ncorda/Github-nicor88/aws-dev:$PYTHONPATH

python cloudformation/cli.py --action $1 --aws-profile nicor88-aws-dev --template-generator $2