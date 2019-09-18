#!/bin/sh
#from recount-pump's workflow/common image wrangling scripts

IMAGE=quay.io/broadsword/snaptron_tests

docker pull --all-tags $* ${IMAGE}
