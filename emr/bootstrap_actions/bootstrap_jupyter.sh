#!/usr/bin/env bash
set -x -e

JUPYTER_PASSWORD=${1:-"myJupyterPassword"}
NOTEBOOK_DIR=${2:-"s3://myS3Bucket/notebooks/"}

# home backup
if [ ! -d /mnt/home_backup ]; then
  sudo mkdir /mnt/home_backup
  sudo cp -a /home/* /mnt/home_backup
fi

# mount home to /mnt
if [ ! -d /mnt/home ]; then
  sudo mv /home/ /mnt/
  sudo ln -s /mnt/home /home
fi

# Install conda
wget https://repo.continuum.io/miniconda/Miniconda3-4.2.12-Linux-x86_64.sh -O /home/hadoop/miniconda.sh \
    && /bin/bash ~/miniconda.sh -b -p $HOME/conda

echo '\nexport PATH=$HOME/conda/bin:$PATH' >> $HOME/.bashrc && source $HOME/.bashrc

conda config --set always_yes yes --set changeps1 no

conda install conda=4.2.13

conda config -f --add channels conda-forge
conda config -f --add channels defaults

conda install hdfs3 findspark ujson jsonschema toolz boto3 py4j numpy pandas==0.19.2

# cleanup
rm ~/miniconda.sh

echo bootstrap_conda.sh completed. PATH now: $PATH
export PYSPARK_PYTHON="/home/hadoop/conda/bin/python3.5"

############### -------------- master node -------------- ###############

IS_MASTER=false
if grep isMaster /mnt/var/lib/info/instance.json | grep true;
then
  IS_MASTER=true

  ### install dependencies for s3fs-fuse to access and store notebooks
  sudo yum install -y git
  sudo yum install -y libcurl libcurl-devel graphviz cyrus-sasl cyrus-sasl-devel readline readline-devel gnuplot
  sudo yum install -y automake fuse fuse-devel libxml2-devel

  # extract BUCKET and FOLDER to mount from NOTEBOOK_DIR
  NOTEBOOK_DIR="${NOTEBOOK_DIR%/}/"
  BUCKET=$(python -c "print('$NOTEBOOK_DIR'.split('//')[1].split('/')[0])")
  FOLDER=$(python -c "print('/'.join('$NOTEBOOK_DIR'.split('//')[1].split('/')[1:-1]))")

  echo "bucket '$BUCKET' folder '$FOLDER'"

  cd /mnt
  git clone https://github.com/s3fs-fuse/s3fs-fuse.git
  cd s3fs-fuse/
  ls -alrt
  ./autogen.sh
  ./configure
  make
  sudo make install
  sudo su -c 'echo user_allow_other >> /etc/fuse.conf'
  mkdir -p /mnt/s3fs-cache
  mkdir -p /mnt/$BUCKET
  /usr/local/bin/s3fs -o allow_other -o iam_role=auto -o umask=0 -o url=https://s3.amazonaws.com  -o no_check_certificate -o enable_noobj_cache -o use_cache=/mnt/s3fs-cache $BUCKET /mnt/$BUCKET

  ### Install Jupyter Notebook with conda and configure it.
  echo "installing python libs in master"
  # install
  conda install jupyter

  # install visualization libs
  conda install matplotlib plotly bokeh

  # install scikit-learn stable version
  conda install --channel scikit-learn-contrib scikit-learn==0.18

  # jupyter configs
  mkdir -p ~/.jupyter
  touch ls ~/.jupyter/jupyter_notebook_config.py
  HASHED_PASSWORD=$(python -c "from notebook.auth import passwd; print(passwd('$JUPYTER_PASSWORD'))")
  echo "c.NotebookApp.password = u'$HASHED_PASSWORD'" >> ~/.jupyter/jupyter_notebook_config.py
  echo "c.NotebookApp.open_browser = False" >> ~/.jupyter/jupyter_notebook_config.py
  echo "c.NotebookApp.ip = '*'" >> ~/.jupyter/jupyter_notebook_config.py
  echo "c.NotebookApp.notebook_dir = '/mnt/$BUCKET/$FOLDER'" >> ~/.jupyter/jupyter_notebook_config.py
  echo "c.ContentsManager.checkpoints_kwargs = {'root_dir': '.checkpoints'}" >> ~/.jupyter/jupyter_notebook_config.py

  ### Setup Jupyter deamon and launch it
  cd ~
  echo "Creating Jupyter Daemon"

  sudo cat <<EOF > /home/hadoop/jupyter.conf
description "Jupyter"

start on runlevel [2345]
stop on runlevel [016]

respawn
respawn limit 0 10

chdir /mnt/$BUCKET/$FOLDER

script
  sudo su - hadoop > /var/log/jupyter.log 2>&1 <<BASH_SCRIPT
        export PYSPARK_DRIVER_PYTHON="/home/hadoop/conda/bin/jupyter"
        export PYSPARK_DRIVER_PYTHON_OPTS="notebook --log-level=INFO"
        export PYSPARK_PYTHON=/home/hadoop/conda/bin/python3.5
        export JAVA_HOME="/etc/alternatives/jre"
        pyspark
  BASH_SCRIPT

end script
EOF

  sudo mv /home/hadoop/jupyter.conf /etc/init/
  sudo chown root:root /etc/init/jupyter.conf

  sudo initctl reload-configuration

  # start jupyter daemon
  echo "Starting Jupyter Daemon"
  sudo initctl start jupyter

fi
