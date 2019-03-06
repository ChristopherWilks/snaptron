#!/usr/bin/env bash
dirname=$(dirname $0)
screen -d -m -S ${1} ${dirname}/run_snaptron_compilation.sh ${dirname}/${1}_snaptron ${1}_snaptron_server
