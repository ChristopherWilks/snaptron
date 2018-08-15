#!/bin/bash

#Pass in the full path where all the snaptron instances are subdirs
ROOT_PATH=$1
cat ~/snaptron_instances.txt | perl -ne 'chomp; $e=$_; $e1="snaptron"; $e1=$e."_snaptron" if($e ne "snaptron"); $e2=$e1."_server"; `screen -d -m -S $e ./run_snaptron_compilation.sh '${ROOT_PATH}'/$e1 $e2`;'
