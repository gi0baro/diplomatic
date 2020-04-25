FROM node:10-alpine

RUN apk --no-cache add --virtual native-deps \
  g++ gcc git libgcc libstdc++ linux-headers make python

WORKDIR /root
