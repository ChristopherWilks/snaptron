#!/bin/sh
# Build base image, starting from vanilla Docker debian, with all dependencies

docker build --tag snaptron .
