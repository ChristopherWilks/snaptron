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
    def __init__(self,cmds,stdout=subprocess.PIPE,shell=False,bufsize=-1):
        self.cmds = cmds
        self.stdout = stdout
        self.shell = shell
        self.bufsize = bufsize
        self.extern_procs = [subprocess.Popen(cmd, stdout=self.stdout, shell=self.shell, bufsize=self.bufsize) for cmd in self.cmds]
        self.idx = 0

    def __iter__(self):
        return self

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
