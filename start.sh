#!/bin/bash
app="cryptoopportunityservice"
docker stop ${app}
docker rm ${app}
docker rmi ${app}
docker build -t ${app} .
docker run -d -p 5002:5002 \
  --name=${app} \
  -v $PWD:/app ${app}
read -n1 -s