#!/usr/bin/env python2.7

# This file is part of Snaptron.
#
# Snaptron is free software: you can redistribute it and/or modify
# it under the terms of the 
#
#    The MIT License
#
#    Copyright (c) 2016-  by Christopher Wilks <broadsword@gmail.com> 
#                         and Ben Langmead <langmea@cs.jhu.edu>
#
#    Permission is hereby granted, free of charge, to any person obtaining
#    a copy of this software and associated documentation files (the
#    "Software"), to deal in the Software without restriction, including
#    without limitation the rights to use, copy, modify, merge, publish,
#    distribute, sublicense, and/or sell copies of the Software, and to
#    permit persons to whom the Software is furnished to do so, subject to
#    the following conditions:
#
#    The above copyright notice and this permission notice shall be
#    included in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
#    BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
#    ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#    SOFTWARE.

import sys
import subprocess
import shlex

class SnaptronServerIterator():
    def __init__(self,cmds,stdout=subprocess.PIPE,shell=False,bufsize=-1,direct_output=False):
            
        self.cmds = cmds
        self.stdout = stdout
        #performance trick, pipe output from subprocess directly to this process's output
        #to avoid the cost of python line processing
        if direct_output:
            self.stdout = sys.stdout
        self.shell = shell
        self.bufsize = bufsize
        #used to run them in parallel, but that's a bad idea because:
        #1) results will come back in random order
        #2) we need to control the number of potential processes spun up by any given query (so for now we'll keep this at 1)
        if direct_output:
            for cmd in self.cmds:
                extern_proc = subprocess.Popen(cmd, shell=self.shell, bufsize=self.bufsize)
                extern_proc.wait() 
        else:
            #TODO: stop this running in parallel for the above cited reasons, but will need to handle
            #the sequential nature in the next() method
            self.extern_procs = [subprocess.Popen(cmd, stdout=self.stdout, shell=self.shell, bufsize=self.bufsize) for cmd in self.cmds]
        self.idx = 0

    def __iter__(self):
        return self

    #this is only used if the self.stdout isn't directed to the current process's sys.stdout
    #i.e. direct_output is False
    def next(self):
        line = self.extern_procs[self.idx].stdout.readline()
        if line == '':
            exitc=self.extern_procs[self.idx].wait() 
            if exitc != 0:
                raise RuntimeError("%s returned non-0 exit code\n" % (self.cmds[self.idx]))
            self.idx+=1
            if self.idx >= len(self.extern_procs):
                raise StopIteration
            line = self.extern_procs[self.idx].stdout.readline()
        return line
