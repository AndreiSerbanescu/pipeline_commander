FROM nvidia/cuda:latest

WORKDIR /app

# Installing Python3 and Pip3
RUN apt-get update
RUN apt-get update && apt-get install -y python3-pip
RUN pip3 install setuptools pip --upgrade --force-reinstall

RUN pip3 install sklearn
RUN pip3 install matplotlib
RUN pip3 install SimpleITK


RUN apt-get install curl -y #debugging
RUN apt-get install vim -y #debugging

# Install dependencies for generating report
RUN pip3 install pandoc

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y texlive-latex-base
RUN apt-get install -y texlive-latex-extra
RUN apt-get install -y texlive-pictures
RUN apt-get install -y texlive-fonts-recommended
RUN pip3 install pdflatex
RUN apt-get install -y pandoc

RUN pip3 install requests
RUN pip3 install pillow

RUN mkdir /app/src
COPY files/ /app/src/