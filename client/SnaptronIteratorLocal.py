#!/usr/bin/env python2.7
import sys
import subprocess
from SnaptronIterator import SnaptronIterator
import clsnapconf

SCRIPT_PATH='../'
#SCRIPT_PATH=''
ENDPOINTS={'snaptron':'snaptron.py','sample':'snample.py','annotation':'snannotation.py','density':'sdensity.py','breakpoint':'sbreakpoint.py'}

class SnaptronIteratorLocal(SnaptronIterator):

    def __init__(self,query_param_string,endpoint):
        SnaptronIterator.__init__(self,query_param_string,endpoint) 
        
        self.construct_query_string(query_param_string,endpoint)
        self.execute_query_string(self.cmd)
    
    def construct_query_string(self,query_param_string,endpoint):
        self.cmd = ['python','%s%s' % (SCRIPT_PATH,ENDPOINTS[endpoint]), query_param_string]
        return self.cmd

    def execute_query_string(self,query_string):
        #sys.stderr.write("executing %s\n" % (query_string))
        self.subp = subprocess.Popen(query_string,shell=False,stderr=subprocess.PIPE,stdout=subprocess.PIPE,stdin=None)
        self.response = self.subp.stdout
        self.errors = self.subp.stderr
        return self.response
    
    def fill_buffer(self):
        #extend parent version to make sure we close gracefully
        lines_read = SnaptronIterator.fill_buffer(self)
        if lines_read > 0:
            return lines_read
        self.subp.wait()
        errors = self.errors.read()
        if len(errors) > 0:
            sys.stderr.write(errors)
            raise RuntimeError("error from local command call %s" % (self.cmd))
        return 0

if __name__ == '__main__':
    sIT = SnaptronIteratorLocal('regions=chr2:29446395-30142858&contains=1&rfilter=samples_count>:100&rfilter=annotated:1','snaptron')
    for record in sIT:
        print (record)

