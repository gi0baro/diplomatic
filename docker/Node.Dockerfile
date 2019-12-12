FROM node:10-alpine

MAINTAINER gi0baro

run apk --no-cache add --virtual native-deps \
  g++ gcc git libgcc libstdc++ linux-headers make python

WORKDIR /root
