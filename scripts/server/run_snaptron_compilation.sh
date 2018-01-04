#!/bin/bash

cd $1
source ./python/bin/activate
./$2 --no-daemon
