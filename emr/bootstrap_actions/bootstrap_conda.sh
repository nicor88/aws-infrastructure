#!/usr/bin/env bash

# Install conda
wget https://repo.continuum.io/miniconda/Miniconda3-4.3.21-Linux-x86_64.sh -O /home/hadoop/miniconda.sh \
    && /bin/bash ~/miniconda.sh -b -p $HOME/conda

conda config --set always_yes yes --set changeps1 no
conda config -f --add channels conda-forge
conda config -f --add channels defaults

# install libs
conda install hdfs3 findspark ujson jsonschema toolz boto3 py4j numpy pandas==0.19.2
