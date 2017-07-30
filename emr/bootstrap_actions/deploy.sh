#!/usr/bin/env bash

SRC=$1
DST=$2

# generic deployment, it take a source from s3 and deploy to a specific destination in each node of the cluster
aws s3 cp --recursive $SRC $DST
