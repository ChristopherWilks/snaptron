#!/usr/bin/env python2.7
import urllib2
import clsnapconf

class SnaptronIterator():

    def __init__(self,query_param_string,endpoint):
        self.buffer_size = clsnapconf.BUFFER_SIZE_BYTES
        self.query_param_string = query_param_string
        self.endpoint = endpoint

        self.idx = -1
        self.total_count = 0
        self.lines = []

        self.next = self.__next__

    def __iter__(self):
        return self
    
    def __next__(self):
        self.idx+=1
        lines_read = 0
        if self.idx >= len(self.lines):
            lines_read = self.fill_buffer()
            self.total_count += lines_read
            self.idx=0;
        if self.idx != 0 or lines_read > 0:
            return self.lines[self.idx]
        raise StopIteration

    def fill_buffer(self):
        buf_ = self.response.read(self.buffer_size)
        if buf_ is None or buf_ == '':
            return 0
        bufs = [buf_]
        last_char = buf_[-1]
        #top up to next newline
        while(last_char != None and last_char != '\n'):
            last_char = self.response.read(1)
            bufs.append(last_char)
        buf_ = "".join(bufs)
        #get rid of last newline so we dont get an emtpy string as a last array element
        if buf_[-1] == '\n':
            buf_ = buf_[:-1]
        self.lines = buf_.split("\n")
        return len(self.lines)
