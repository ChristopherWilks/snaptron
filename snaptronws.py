#!/usr/bin/env python2.7

import sys
import re
import os
import subprocess
import datetime
import logging
from logging import handlers
import urllib2
import urllib
import base64
import hashlib
import urlparse
import tempfile
from collections import namedtuple
import json
from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read
import errno
import time

#size for the OS buffer on the input pipe reading from samtools output
#CMD_BUFFER_SIZE=16777216
#CMD_BUFFER_SIZE=4194304
PYTHON_PATH='/data/gigatron/snaptron/python/bin/python'
LOCAL_APP = '/data/gigatron/snaptron/snaptron.py'
CMD_BUFFER_SIZE = -1
#in seconds, so just under an hour to cache the authorization result for a specific token/acm_url
TIME_TO_MEMOIZE_AUTH_RESULT=3500
#size of samtools read,can impact performance in a major way
#READ_SIZE=1048576
#a low max for what we want to pass to samtools for start/end coordinates, otherwise samtools will return everything
MAX_COORDINATE_DIGITS = 11
READ_SIZE = 16777216
#for test read much smaller chunks
#READ_SIZE=32

logger = logging.getLogger("snaptronws")
logger.setLevel(logging.INFO)
lHandler = logging.StreamHandler()
#sHandler = logging.handlers.SysLogHandler()
lHandler.setLevel(logging.DEBUG)
#sHandler.setLevel(logging.DEBUG)
logger.addHandler(lHandler)

#passes back a stream, either binary or text (its agnostic) in READ_SIZE chunks
#Iterator for SamTools (ST)
class StreamingResponseIterator:
    def __init__(self, start_response, stream_subproc, request_id, read_size=READ_SIZE):
        self.start_response = start_response
        self.stream_subproc = stream_subproc
        self.request_id = request_id
        if self.request_id is not None:
            self.content_hash = hashlib.md5()
        self.done = False
        self.closed = False
        self.read_size = read_size
        self.stderr = []

    def __iter__(self):
        return self
    
    def _read_last_stderr(self):
        flgs = fcntl(self.stream_subproc.stderr, F_GETFL)
        #remove the O_NONBLOCK flag
        fcntl(self.stream_subproc.stderr, F_SETFL, flgs ^ O_NONBLOCK)
        stderr = self.stream_subproc.stderr.read()
        #hit EOF
        if not stderr:
            return
        self.stderr.append(stderr)

    def _read_non_blocking_stderr(self):
        #keep reading from stderr in case we pick 
        #up one or more (but we don't block)
        while(True):
            try:
                stderr = read(self.stream_subproc.stderr.fileno(), READ_SIZE)
                #hit EOF
                if not stderr:
                    break
                self.stderr.append(stderr)
            except OSError, e:
                #since we're non-blocking we can ignore this
                if e.args[0] == errno.EAGAIN:
                        return
                else:
                    raise

    def _wait(self):
        if self.closed:
            return
        self._read_last_stderr()
        self.stream_subproc.wait()
        self.closed = True
        if self.stream_subproc.returncode != 0 or len(self.stderr) > 0:
            errors = []
            logger.error("in _wait, found an error")
            stderr = "".join(self.stderr)
            for line in stderr.split("\n"):
                errors.append("%s:%s" % (LOCAL_APP, line.rstrip()))
                logger.error("%s:%s" % (LOCAL_APP, line.rstrip()))
            #alert the server to the error by THROWING AN EXCEPTION (not re-calling start_response)
            raise Exception("%s failed on %s" % (LOCAL_APP, ":::".join(errors)))

    def _terminate(self):
        if self.closed:
            return
        #force close as this is no longer the happy path
        self.stream_subproc.kill()
        self.closed = True

    def next(self):
        if self.done:
            raise StopIteration
        #read next "chunk" from stream output, stream and return, 
        #this will block if more data is coming and < READ_SIZE
        chunk = self.stream_subproc.stdout.read(READ_SIZE)
        if chunk == "":
            self.done = True
            self._wait()
            if self.request_id is not None:
                with open(os.path.join(tempfile.gettempdir(), "snaptron.%s" % self.request_id), "w") as hashfile:
                    hashfile.write(self.content_hash.hexdigest())
            raise StopIteration
        #add this to the running checksum
        if self.request_id is not None:
            self.content_hash.update(chunk)
        #read any errors coming through
        self._read_non_blocking_stderr()
        return chunk

    def close(self):
        self._terminate()

#used to actually implement the logic to force a stream error for testing purposes
class DebugStreamIterator():
    def __init__(self, si):
        self.si = si
        self.FIRST = True

    def __iter__(self):
        return self

    def close(self):
        self.si.close()

    #for debugging only, only used when DebugStreamIterator is being used
    def next(self):
        #0-length chunk debugging
        logger.debug("not yet raising force_stream_error exception in DebugStreamIterator\n")
        if not self.FIRST:
            logger.debug("raising force_stream_error exception in DebugStreamIterator\n")
            raise Exception("DEBUG CHUNKED ENCODING ERROR")
        self.FIRST = False
        return self.si.next()

#these first are just the methdos mapping to various http return codes
def bad_request(start_response, msg):
    #status = "400 Bad Request:%s" % (msg)
    status = "400 Bad Request:%s" % (msg)
    sys.stderr.write("%s\n" % (status))
    status_response = "%s\n%s\n" % (status,support_blurb)
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return status_response


def bad_request_partial(start_response, msg, file_size):
    status = "416 Requested Range Not Satisfiable:%s" % (msg)
    sys.stderr.write("%s\n" % (status))
    status_response = "%s\n%s\n" % (status,support_blurb)
    response_headers = [('Content-type', 'text/plain'), ('Content-Range', "bytes */%s" % (file_size))]
    start_response(status, response_headers)
    return status_response


def unauthorized(start_response):
    status = "401 Unauthorized"
    sys.stderr.write("%s\n" % (status))
    status_response = "%s\n%s\n" % (status,support_blurb)
    response_headers = [('Content-type', 'text/plain'), ('WWW-Authenticate', 'Basic realm="CGHubSlicer"')]
    start_response(status, response_headers)
    return status_response


def forbidden(start_response):
    status = "403 Forbidden"
    sys.stderr.write("%s\n" % (status))
    status_response = "%s\n%s\n" % (status,support_blurb)
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return status_response


def custom_response(start_response, code, msg):
    status = "%s %s" % (code,msg)
    sys.stderr.write("%s\n" % (status))
    status_response = "%s\n%s\n" % (status,support_blurb)
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return status_response


def internal_server_error(start_response, msg):
    status = "500 Internal Server Error:%s" % (msg)
    sys.stderr.write("%s\n" % (status))
    status_response = "%s\n%s\n" % (status,support_blurb)
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return status_response


def run_command(cmd_and_args):
    logger.info("Running: %s" % (" ".join(cmd_and_args)))
    sproc = subprocess.Popen(cmd_and_args, bufsize=CMD_BUFFER_SIZE, 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    #we need to make sure that reading from the STDERR pipe 
    #is NOT going to block since we don't know if we'll get errors, or not
    #we DO want to block on the STDOUT though
    flgs = fcntl(sproc.stderr, F_GETFL)
    fcntl(sproc.stderr, F_SETFL, flgs | O_NONBLOCK)
    return sproc


RANGE_PATTERN = re.compile(r'^[0-9a-zA-Z_\-]+:\d+-\d+$')
def query(query, add_checksum=True):

    args = [PYTHON_PATH, LOCAL_APP]
    #get the one or more range tuples (expect chr:start-end) 
    ranges = query.get('range', [])

    #if slices was called, IT MUST have at least one range 
    if len(ranges) == 0:
        raise urllib2.HTTPError(None, 400, "must submit at least one range when calling slices endpoint", None, None)

    done = False
    for range in ranges:
        #we should be finished with the ranges, if the user submitted more than expected, raise an error
        if done:
            raise urllib2.HTTPError(None, 400, "submitted more than expected number of ranges", None, None)
        #must be the expected format
        if RANGE_PATTERN.search(range) is None:
            raise urllib2.HTTPError(None, 400, "submitted one or more ranges in an unsupported format", None, None)
        (chr, start_end) = range.split(":")
        (start, end) = start_end.split("-")
        #must not be above MAX_COORDINATE_DIGITS otherwise samtools will start returning everything
        if len(start) > MAX_COORDINATE_DIGITS or len(end) > MAX_COORDINATE_DIGITS:
            raise urllib2.HTTPError(None, 400,
                                    "The start or the end coordinate (or both) of this range %s is exceeds %s" % (
                                    range, str(MAX_COORDINATE_DIGITS)), None, None)
        #also must not have swapped start and end, otherwise samtools will return everything
        if int(start) > int(end):
            raise urllib2.HTTPError(None, 400, "The start coordinate > the end coordinate in this range %s" % range,
                                    None, None)
        args.append(range)

    #hash the unique parts of the command for checksum service
    request_id = None
    #if add_checksum:
        #request_id = get_request_id(analysis_id, "slices", "stream", query)

    return args, request_id


def translate_range_query(squery):
    squery=re.sub(r'AND',r'|',squery)
    squery=re.sub(r'GT',r'>',squery)
    squery=re.sub(r'GE',r'>=',squery)
    squery=re.sub(r'LE',r'<=',squery)
    squery=re.sub(r'LT',r'<',squery)
    squery=re.sub(r'\$',r':',squery)
    squery=re.sub(r'EQ',r'=',squery)
    squery=re.sub(r'!',r'!=',squery)
    return squery

#cant have anything else in the data path or its probably a security issue
READ_SIZE_PATTERN = re.compile(r'^\d+$')
def snaptron_endpoint(environ, start_response):
    http_error_map = {400: bad_request, 401: unauthorized, 403: forbidden, 500: internal_server_error}
    query_string = environ.get('QUERY_STRING')
    query = urlparse.parse_qs(environ.get('QUERY_STRING'))
    #first log message (outside of errors) so put in a newline
    logger.info("\nQUERY_STRING %s" % query_string)

    add_checksum = False
    #if function_path == 'header' or function_path == 'slices':
    #    add_checksum = True

    logger.debug("REQUEST ENVIRONMENT:")
    for (key, val) in environ.iteritems():
        logger.debug("key=%s val=%s" % (key, val))
        #see if we're in test/debug mode for the chunked error
    try:
        force_stream_error = str(environ['HTTP_X_FORCE_STREAM_ERROR'])
    except KeyError:
        force_stream_error = "0"

    read_size = READ_SIZE
    #see if the read_size is being overriden (as in a test server is calling this)
    if 'read_size' in environ:
        read_size = str(environ['read_size'])
        if READ_SIZE_PATTERN.search(read_size) is None:
            return bad_request(start_response, "bad read_size in environment")
    logger.info("READ_SIZE=%s" % read_size)
    read_size = int(read_size)

    rquery=query.get('rquery', [])
    logger.info("BEFORE rquery=%s" % (rquery[0]))
    rquery = translate_range_query(rquery[0])
    logger.info("AFTER rquery=%s" % (rquery))
    #now get the sample part of this query
    #s2query=query.get('squery', [])
    #args=[PYTHON_PATH, LOCAL_APP, "'%s'" % (rquery)]
    args=[PYTHON_PATH, LOCAL_APP, rquery]
    #create subprocess run object 
    sproc = run_command(args)

    #do the response 
    status = "200 OK"
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    request_id=None
    si = StreamingResponseIterator(start_response, sproc, request_id, read_size)
    if force_stream_error == str(1):
        logger.debug("bforce_stream_error %s\n" % force_stream_error)
        si = DebugStreamIterator(si)
    return si

#only for basic testing
if __name__ == '__main__':
    rquery=r'chr6$1-10000000ANDsamples_countEQ5AND'
    logger.info("BEFORE rquery=%s" % (rquery))
    rquery = translate_range_query(rquery)
    logger.info("AFTER rquery=%s" % (rquery))
    #sproc = run_command([PYTHON_PATH, LOCAL_APP, 'chr6:1-10000000|samples_count=5|','1'])
    sproc = run_command([PYTHON_PATH, LOCAL_APP, rquery])
    itr=StreamingResponseIterator(None,sproc,None)
    chunk=itr.next();
    while(chunk):
        sys.stderr.write(chunk + "\n")
        chunk=itr.next();
