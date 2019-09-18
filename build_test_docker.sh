#!/bin/bash
# Build base image, starting from vanilla Docker debian, with all dependencies

bdir=$(dirname $0)
docker build --tag quay.io/broadsword/snaptron_tests -f tests/Dockerfile $bdir
