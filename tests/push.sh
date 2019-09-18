#!/bin/sh

IMAGE=quay.io/broadsword/snaptron_tests
VER=$(cat ver.txt)

docker push $* ${IMAGE}:${VER}
docker push $* ${IMAGE}:latest
