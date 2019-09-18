#!/bin/bash
# Run previously built *test* Snaptron Docker image as a container
dir=$(dirname $0)
/bin/bash -x ${dir}/pull.sh
docker run --rm -p 21656:1656 -p 2080:80 -i -t --name test_snaptron quay.io/broadsword/snaptron_tests
