FROM python:3.6.4

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y libjpeg-dev libfreetype6-dev zlib1g-dev

# install python requirements
RUN mkdir /usr/src/app
ADD requirements.txt /usr/src/app
RUN pip install -r /usr/src/app/requirements.txt --src /usr/src/app

RUN mkdir /app
WORKDIR /app
