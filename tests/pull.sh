#!/bin/sh

IMAGE=quay.io/broadsword/snaptron_tests

docker pull --all-tags $* ${IMAGE}
