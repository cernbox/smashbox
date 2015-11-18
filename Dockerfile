FROM ubuntu:14.04

MAINTAINER Piotr Mrowczynski <piotr.mrowczynski@yahoo.com>
RUN apt-get install wget -y
RUN sh -c "echo 'deb http://download.opensuse.org/repositories/isv:/ownCloud:/desktop/xUbuntu_14.04/ /' >> /etc/apt/sources.li$
RUN wget http://download.opensuse.org/repositories/isv:ownCloud:desktop/xUbuntu_14.04/Release.key
RUN apt-key add - < Release.key
RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install git-all -y
RUN sudo apt-get install owncloud-client -y
RUN apt-get install python-netifaces -y
