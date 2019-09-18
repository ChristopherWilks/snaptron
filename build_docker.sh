#!/bin/sh
# Build base image, starting from vanilla Docker debian, with all dependencies

bdir=$(dirname $0)
docker build --tag snaptron $bdir
