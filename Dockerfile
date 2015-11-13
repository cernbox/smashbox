FROM ubuntu:14.04
MAINTAINER Piotr Mrowczynski <piotr.mrowczynski@yahoo.com>
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install git-all -y