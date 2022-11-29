#!/bin/bash

if [ ! -n "$1" ]; then
  echo "Prefix name as first arg is required to keep it tidy"
  exit
fi

PREFIX=$1
CONTAINER_NAME=python-stress-test
VERSION=v0.1
pid=0


sigint_handler() {
  if [ $pid -ne 0 ]; then
    echo -e '\nStopping container...'
    #docker kill --signal=SIGINT $(docker ps | grep $CONTAINER_NAME | awk '{print $1}')
    docker exec $(docker ps | grep $CONTAINER_NAME | awk '{print $1}') kill -TERM -$$
  else
    sleep 3
  fi
  #exit
}

#trap 'sleep 3; exit' SIGINT


docker build -t $CONTAINER_NAME:$VERSION .

DATA_DIR=data
ERROR_LOG_DIR=error-logs
DATE_FORMAT=+%Y-%m-%d-%H:%M:%S

[ ! -d $DATA_DIR ] && mkdir $DATA_DIR
[ ! -d $DATA_DIR/$ERROR_LOG_DIR ] && mkdir $DATA_DIR/$ERROR_LOG_DIR

OUTPUT=$PREFIX-$(date $DATE_FORMAT)-latencies.csv

docker run --add-host host.docker.internal:host-gateway $CONTAINER_NAME:$VERSION 2> $DATA_DIR/$ERROR_LOG_DIR/$PREFIX-$(date $DATE_FORMAT)-req-errors.txt 1> $DATA_DIR/$OUTPUT & pid="$!"; trap 'sigint_handler' SIGINT
#####trap "echo -e '\nStopping container...\n'" 2


sleep 1
tail -f $DATA_DIR/$OUTPUT

