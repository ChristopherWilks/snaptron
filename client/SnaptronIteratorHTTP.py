#!/usr/bin/env python2.7
import urllib2
from SnaptronIterator import SnaptronIterator
import clsnapconf

ENDPOINTS={'snaptron':'snaptron','sample':'sample','annotation':'annotation','density':'density'}

class SnaptronIteratorHTTP(SnaptronIterator):

    def __init__(self,query_param_string,endpoint):
        SnaptronIterator.__init__(self,query_param_string,endpoint) 

        self.SERVICE_URL=clsnapconf.SERVICE_URL
        self.ENDPOINTS=ENDPOINTS
        self.construct_query_string()
        self.execute_query_string()

    def construct_query_string(self):
        self.query_string = "%s/%s?%s" % (self.SERVICE_URL,self.ENDPOINTS[self.endpoint],self.query_param_string)
        return self.query_string

    def execute_query_string(self):
        print(self.query_string)
        self.response = urllib2.urlopen(self.query_string)
        return self.response


if __name__ == '__main__':
    it = SnaptronIteratorHTTP('regions=chr1:1-100000&rfilter=samples_count>:5','snaptron')
    for r in it:
        print("%s" % r)
