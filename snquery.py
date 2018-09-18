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
import re
import subprocess
import shlex
import snapconf
import snapconfshared 
import snaputil
from sniterator import SnaptronServerIterator

#for speedy multi-sample ID searching per jx
import ahocorasick

RegionArgs = snapconfshared.RegionArgs
default_region_args = snapconfshared.default_region_args
logger = default_region_args.logger

EITHER_START=snapconfshared.EITHER_START
EITHER_END=snapconfshared.EITHER_END
return_formats = snaputil.return_formats

#return formats:
TSV=snapconfshared.TSV
UCSC_BED=snapconfshared.UCSC_BED
UCSC_URL=snapconfshared.UCSC_URL

def build_sid_ahoc_queries(sample_ids):
    acs = ahocorasick.Automaton()
    #need to add "," and ":" to make sure we dont match coverage counts or within other IDs
    [acs.add_word(","+sid+":", sid) for sid in sample_ids]
    acs.make_automaton()
    return acs

class RunExternalQueryEngine:

    def __init__(self,cmd,qargs,rangeq,snaptron_ids,region_args=default_region_args,additional_cmd=""):
        self.direct_output = False
        self.cmd = cmd
        self.qargs = qargs
        self.ra = region_args
        self.snaptron_ids = snaptron_ids
        #this trumps whatever stream_back instructions we were given
        if self.ra.result_count:
            self.ra = self.ra._replace(stream_back=False)
            self.ra = self.ra._replace(save_introns=True)

        self.filter_by_introns = (self.ra.intron_filter != None and len(self.ra.intron_filter) > 0)
        self.filter_by_samples = (self.ra.sample_filter != None and len(self.ra.sample_filter) > 0)

        (header_method,streamer_method) = return_formats[self.ra.return_format]
        self.header = header_method(sys.stdout,region_args=self.ra,interval=self.qargs)
        self.streamer_method = streamer_method
        #exit early as we only want the ucsc_url
        if self.ra.return_format == UCSC_URL:
            return

        if cmd == snapconf.TABIX:
            self.delim = '\t'
            m = snapconf.TABIX_PATTERN.search(self.qargs)
            self.start = int(m.group(2))
            self.end = int(m.group(3))
            self.range_filters = self.ra.range_filters if self.ra.range_filters is not None and len(self.ra.range_filters) > 0 else None
            additional_cmd = ''
            if len(self.ra.additional_cmd) > 0:
                additional_cmd = " | %s" % (self.ra.additional_cmd)
            self.ra = self.ra._replace(tabix_db_file = "%s/%s" % (snapconf.TABIX_DB_PATH,self.ra.tabix_db_file))
            self.full_cmd = "%s %s %s %s" % (cmd,self.ra.tabix_db_file,self.qargs,additional_cmd)
            self.cmds = []
            if self.ra.app == snapconf.BASES_APP:
                self.chrom = m.group(1)
                #might be using a different version of Tabix for bases (e.g. using zstd for compression)
                cmd = snapconf.TABIX_BASES
                #offset for start at 0 in BigWig derived bases
                qargs_and_region_files = snaputil.map_region2files(self.chrom,self.start,self.end)
                if self.ra.return_format == snapconfshared.UCSC_WIG or bool(self.ra.calc):
                    r = self.ra
                    #additional_cmd += " | %s -a %s -o %s -l \"%s" % (snapconfshared.CALC_PATH,r.calc_axis,r.calc_op,r.label)
                    #add label later (if it's passed in)
                    additional_cmd += " | %s -a %s -o %s" % (snapconfshared.CALC_PATH,r.calc_axis,r.calc_op)
                    self.direct_output = True
                self.start-=1
                for (qargs,region_file) in qargs_and_region_files:
                    #need to set the region for each split so the client knows how to re-assemble the splits
                    additional_cmd_ = additional_cmd
                    if self.ra.return_format == snapconfshared.UCSC_WIG or bool(self.ra.calc):
                        qargs_ = qargs.replace(':','|')
                        qargs_ = qargs_.replace('-','|')
                        #label is ignored if doing axis=1 (col summaries)
                        #since each row will have the chr:start-end printed out for it
                        additional_cmd_ += " -l \""+qargs_+"|"+r.label+"\""
                    self.cmds.append("%s %s %s %s" % (cmd,region_file,qargs,additional_cmd_))
                    logger.debug("running %s %s %s\n" % (self.cmds[-1],region_file,qargs))
            else:
                self.cmds.append(self.full_cmd)
            #self.full_cmd = "%s %s %s | cut -f %d- %s" % (cmd,self.ra.tabix_db_file,self.qargs,self.ra.cut_start_col,additional_cmd)
            #NOTE: we use shell=True due to the ease of including "additional_cmd" which is only used by snannotation to limit gene models returned by tabix
            #maybe we should consider doing this differently, however, self.qargs is enforced to be a strict chr:start-end pattern,
            #and the rest of the arguments are set internally, so I think we avoid potential injection attacks here
            #self.extern_proc = SnaptronServerIterator([self.full_cmd], shell=True)
            self.extern_proc = SnaptronServerIterator(self.cmds, shell=True, direct_output=self.direct_output)

        elif cmd == snapconf.SQLITE:
            self.delim = '\t'
            arguments = []
            where = []
            (chrom,start,end) = snaputil.sqlite3_interval_query_parse(self.qargs,where,arguments,self.ra)
            self.chrom = chrom
            self.start = start
            self.end = end
            snaputil.sqlite3_range_query_parse(rangeq,where,arguments)
            #force sqlite3 to 3 decimal places
            select_fields = snapconfshared.INTRON_HEADER_FIELDS
            select_fields[snapconf.CHROM_COL]='chrom'
            select_fields[snapconf.DONOR_COL]='donor'
            select_fields[snapconf.ACCEPTOR_COL]='acceptor'
            select_fields[snapconf.COV_AVG_COL]="printf('%.3f',coverage_avg)"
            select_fields[snapconf.COV_MED_COL]="printf('%.3f',coverage_median)"
            select = "SELECT %s from intron WHERE %s" % (",".join(select_fields), ' AND '.join(where))
            logger.debug("%s\t%s\n" % (select,arguments))
            query_ = select
            chr_patt = re.compile('(chr)|[+-]')
            for (i,arg_) in enumerate(arguments):
                arg_ = str(arg_)
                if chr_patt.search(arg_):
                    query_ = re.sub('\?',"\'%s\'" % arg_,query_,count=1)
                else:
                    query_ = re.sub('\?',arg_,query_,count=1)
            full_cmd_args = [self.cmd, '-separator \'	\'', self.ra.sqlite_db_file, '"%s"' % query_]
            self.full_cmd = " ".join(full_cmd_args)
            full_cmd_args = shlex.split(self.full_cmd)
            #we never going to use additional range filters because R+F+M will go through tabix
            self.range_filters = None
            logger.debug("%s\n" % (self.full_cmd))
            self.extern_proc = SnaptronServerIterator([full_cmd_args], shell=False)


    def run_query(self):
        ids_found = set()
        sample_set = set()
        if self.direct_output:
            return (ids_found, sample_set)
        #sys.stdout.write("NOT DOING DIRECT OUTPUT\n")
        #exit early as we only want the ucsc_url
        if self.ra.return_format == UCSC_URL:
            return (ids_found,sample_set)
        #for line in self.extern_proc.stdout:
        for line in self.extern_proc:
            fields = line.rstrip().split(self.delim)
            snaptron_id = str(fields[self.ra.id_col])
            lstart = int(fields[self.ra.region_start_col])
            lend = int(fields[self.ra.region_end_col])
            #first attempt to filter by violation of containment (if in effect)
            if self.ra.exact and (lstart != self.start or lend != self.end):
                continue
            #2nd attempt to filter by violation of containment (if in effect)
            if self.ra.contains and (lstart < self.start or lend > self.end):
                continue
            #third attempt to filter by violation of within one end or the other (if in effect)
            if (self.ra.either == EITHER_START and lstart < self.start) or (self.ra.either == EITHER_END and lend > self.end):
                continue
            #now filter, this order is important (filter first, than save ids/print)
            if self.filter_by_introns and snaptron_id not in self.ra.intron_filter and snaptron_id not in self.snaptron_ids:
                continue
            #filter by M (sample IDs), recalculate summaries from subset of samples, and update fields
            samples_found_iter = None
            #TODO: support sample filtering for base-level data?
            if self.ra.sid_search_object is not None:
                samples_found_iter = self.ra.sid_search_object.iter(fields[snapconf.SAMPLE_IDS_COL])
                #check to see if this jx has one or more of the sample IDs
                (found_np, fields) = snaputil.extract_sids_and_covs_from_search_iter(samples_found_iter, fields)
                if fields is None:
                    continue
            #not used unless testing Tabix or doing a R + F + M query
            if (self.cmd == snapconf.TABIX or samples_found_iter is not None) and self.range_filters is not None and snaputil.filter_by_ranges(fields,self.range_filters):
                continue
            #combine these two so we only have to split sample <= 1 times
            if self.ra.save_samples:
                samples = set(fields[snapconf.SAMPLE_IDS_COL].split(","))
                #due to start prefixed "," delete empty string in set
                if '' in samples:
                    samples.remove('')
                sample_set.update(samples)
            #TODO: use samples_found_iter to get a projection of just the samples
            #searched for and then recalculate summary stats
            #filter return stream based on range queries (if any)
            if self.ra.stream_back:
                 if samples_found_iter is not None:
                    self.streamer_method(sys.stdout,None,fields,region_args=self.ra)
                 else:
                    self.streamer_method(sys.stdout,line,fields,region_args=self.ra)
            if self.ra.save_introns:
                ids_found.add(snaptron_id)
        return (ids_found, sample_set)
