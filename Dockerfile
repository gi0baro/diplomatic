FROM python:3.6.1

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y libjpeg-dev libfreetype6-dev zlib1g-dev

# install python requirements
RUN mkdir /home/app
ADD requirements.txt /home/app/
WORKDIR /home/app
RUN pip3 install -r requirements.txt
