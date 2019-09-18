#!/bin/bash
# Run previously built *test* Snaptron Docker image as a container

docker run --rm -p 21656:1656 -p 2080:80 -i -t --name test_snaptron snaptron_tests
