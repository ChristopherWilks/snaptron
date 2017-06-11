#!/bin/sh

# Build base image, starting from vanilla Docker debian, with all dependencies
docker build -t snaptron-attempt -f docker/base/Dockerfile .
