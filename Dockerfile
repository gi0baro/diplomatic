FROM python:3.5

RUN curl -sL https://deb.nodesource.com/setup_6.x | bash -
RUN apt-get install -y nodejs
RUN apt-get install -y libjpeg-dev libfreetype6-dev zlib1g-dev

## TEMP: weppy master
WORKDIR /root
ADD http://www.random.org/strings/?num=10&len=8&digits=on&upperalpha=on&loweralpha=on&unique=on&format=plain&rnd=new uuid
RUN git clone https://github.com/web2py/pydal.git pydal
RUN cd pydal && python3 setup.py install
RUN git clone https://github.com/gi0baro/weppy.git weppy
RUN cd weppy && python3 setup.py install

# install python requirements
RUN mkdir /home/app
ADD requirements.txt /home/app/
WORKDIR /home/app
RUN pip3 install -r requirements.txt
