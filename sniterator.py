#!/usr/bin/env python2.7

# Copyright 2016, Christopher Wilks <broadsword@gmail.com>
#
# This file is part of Snaptron.
#
# Snaptron is free software: you can redistribute it and/or modify
# it under the terms of the 
# Creative Commons Attribution-NonCommercial 4.0 
# International Public License ("CC BY-NC 4.0").
#
# Snaptron is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# CC BY-NC 4.0 license for more details.
#
# You should have received a copy of the CC BY-NC 4.0 license
# along with Snaptron.  If not, see 
# <https://creativecommons.org/licenses/by-nc/4.0/legalcode>.

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
