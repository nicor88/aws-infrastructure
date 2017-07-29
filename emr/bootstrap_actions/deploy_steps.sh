#!/usr/bin/env bash

# deploying steps
aws s3 cp --recursive s3://nicor-dev/emr/steps/ ~/steps
