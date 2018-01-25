FROM ubuntu:16.04
MAINTAINER nicor88

RUN apt-get update
RUN apt-get install -y curl sudo unzip bzip2

# Configure Miniconda
ENV MINICONDA_VER 4.2.12
ENV MINICONDA Miniconda3-$MINICONDA_VER-Linux-x86_64.sh
ENV MINICONDA_URL https://repo.continuum.io/miniconda/$MINICONDA
ENV CONDA_DIR /opt/miniconda

WORKDIR /tmp
RUN curl -L $MINICONDA_URL  -o miniconda.sh
RUN echo $CONDA_DIR
RUN sudo bash miniconda.sh -b -p $CONDA_DIR
RUN rm /tmp/miniconda.sh
RUN $CONDA_DIR/bin/conda install --yes conda==$MINICONDA_VER

# setup conda in the env
ENV PATH $CONDA_DIR/bin:$PATH
