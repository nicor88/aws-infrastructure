#!/usr/bin/env bash

# Install conda
wget https://repo.continuum.io/miniconda/Miniconda3-4.2.12-Linux-x86_64.sh -O /home/hadoop/miniconda.sh
/bin/bash /home/hadoop/miniconda.sh -b -p /home/hadoop/miniconda

# for debug
echo $USER
echo $HOME

# setup conda
echo -e "\nexport PATH=/home/hadoop/miniconda/bin:$PATH" >> /home/hadoop/.bashrc
source /home/hadoop/.bashrc

conda config --set always_yes yes --set changeps1 no
conda config -f --add channels conda-forge
conda config -f --add channels defaults

# install libs
conda install hdfs3 findspark ujson jsonschema toolz boto3 py4j numpy pandas

# cleanup
rm ~/miniconda.sh
