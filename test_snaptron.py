#!/usr/bin/env python2.7
import sys
import os
import operator
from StringIO import StringIO
import unittest

import snapconf
import snapconfshared
import snaputil
import snaptron
import snannotation
import snquery
import sqlite3

snaptron.sconn = sqlite3.connect(snapconfshared.SNAPTRON_SQLITE_DB)
snaptron.snc = snaptron.sconn.cursor()

#set of test interval queries
IQs=['chr1:10160-10161','CD99','chr11:82970135-82997450','chr11:82985784-82989768','chr11:82571908-82571909','chr11:82356629-82403678']
#RQs=['1:100000-100000','1:5-5']
#IRQs are a set of combination of indexes from IQs and RQs
#RQs=[{'length':[snapconfshared.operators['='],54]},{'samples_count':[snapconfshared.operators['='],10]}]
RQs=[{'length':[snapconfshared.operators[':'],54]},{'samples_count':[snapconfshared.operators[':'],10]}]
RQs_flat=['length:54','samples_count:10','coverage_avg>2.0','samples_count>:100','coverage_sum>:1000','samples_count:10000','coverage_avg>20']
IDs=[set(['33401689','33401829']),set(['6','9'])]
#holds the set of intropolis ids for each specific query for the original SRA set of inropolis junctions
EXPECTED_IIDS={
               IQs[0]:set(['0','1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','17','18','19','20','23','24','25','26','27','28','30','31','32','33','34','35','36','37','38','40','41','42','43','44','45','46','47','49','50','51','52','53','54','55','56','57','58','59','60','61','62']),
               IQs[0]+str(RQs[0]):set(['2','17','25']),
               IQs[0]+str(RQs[0])+str(IDs[1]):set([]),
               str(IDs[0]):set(['33401689','33401829']),
               IQs[1]+str(RQs[1]):set(['78227192','78227202','78227987','78227989','78229111','78231526','78231699','78232393','78235012','78238555','78239061','78247688','78248550','78249622','78249624','78249890','78250373','78250933','78251946','78252458','78252790','78256239','78257352','78258005','78258153','78258164','78258305','78258522','78258883','78258923','78259017','78259240','78259358','78259371','78259397','78259704','78259711','78259761','78259763','78259873','78259986','78260267','78260461','78260470','78260487','78260498','78260515','78260523','78260793','78260903','78261109','78261125','78261130','78261266','78261298','78261418','78261508','78261798','78262001','78262049','78262090','78262191','78262200','78262351','78262405','78262516','78262672','78262945','78263190','78263302','78263553','78263837','78263974','78264156','78264181','78264275','78264413']),
               #IQs[2]+str(RQs_flat[1])+str(RQs_flat[2]):set(['7474725','7474726','7475267']),
               IQs[2]+str(RQs_flat[1])+str(RQs_flat[2]):set([]),
               IQs[3]+str(RQs_flat[3])+str(RQs_flat[4]):set(['14075114','14075109']),
               #str(RQs_flat[5])+str(RQs_flat[6]):set(['1900915','17229066','14511883','18158500','19434757'])
               #str(RQs_flat[5])+str(RQs_flat[6]):set(['21266715','59043106']),
               str(RQs_flat[5])+str(RQs_flat[6]):set(['41278365']),
               IQs[4]+str(RQs_flat[3])+str(RQs_flat[4]):set(['14065307']),
               IQs[5]+str(RQs_flat[3])+str(RQs_flat[4]):set(['14065307','14065333'])
              }

def setUpModule():
    pass

def tearDownModule():
    pass

gc = snannotation.GeneCoords()
#shortcuts for snaptron methods used in tests
def run_tabix(intervalq,region_args=snaptron.default_region_args):
    runner = snquery.RunExternalQueryEngine(snapconfshared.TABIX,intervalq,None,set(),region_args=region_args)
    return runner.run_query()

tc = run_tabix
rqp = snaptron.range_query_parser

def run_sqlite3(intervalq,rangeq,snaptron_ids,region_args=snaptron.default_region_args):
    runner = snquery.RunExternalQueryEngine(snapconfshared.SQLITE,intervalq,rangeq,snaptron_ids,region_args=region_args)
    return runner.run_query()

srl = run_sqlite3

sbi = snaptron.search_introns_by_ids
sbg = snaptron.search_by_gene_name

#pjq = snaptron.parse_json_query
pjq = snaptron.process_post_params
pp = snaptron.process_params

qr = snaptron.query_regions
qi = snaptron.query_ids

tdbs = snapconfshared.TABIX_DBS

class TestTabixCalls(unittest.TestCase):
    '''
    check tabix for basic queries (both interval and range including ids)
    def run_tabix(qargs,rquerys,tabix_db,filter_set=None,sample_set=None,filtering=False,print_header=True,debug=True):
    returns an id set if filtering==True
    can also populate sample_set if defined.
    These are true unit tests.
    '''

    def setUp(self):
        pass

    def tearDown(self):
        snaptron.REQ_FIELDS=[]
   
    def itc(self,interval_query,rq=None,range_query=None,filter_set=None,sample_set=None,filtering=False):
        '''wrap the normal run_tabix/search_by_gene_name call to hardcode defaults for interval/gene name querying'''
        if snapconfshared.INTERVAL_PATTERN.search(interval_query):
            ra = snaptron.default_region_args._replace(range_filters=range_query,tabix_db_file=tdbs['chromosome'],intron_filter=filter_set,sample_filter=sample_set,save_introns=filtering) 
            return tc(interval_query,region_args=ra)
        return sbg(gc,interval_query,{'rfilter':[rq]},range_query,intron_filters=filter_set,save_introns=filtering) 
    
    def idc(self,ids,filtering=False):
        '''wrap the normal run_tabix call to hardcode defaults for interval querying AND range filtering'''
        return sbi(ids,None,filtering=filtering)
    
    def idcr(self,ids,range_query):
        '''wrap the normal run_tabix call to hardcode defaults for interval querying AND range filtering'''
        return sbi(ids,range_query)
    

#actual tests 
    def test_basic_json_parsing(self):
        '''tests to see if our json parsing for the original hacky query language works'''
        query = "[{\"intervals\":[\"chr6:1-10000000\"],\"samples_count\":[{\"op\":\":\",\"val\":5}],\"ids\":[1,4]}]"
        (iq,rq,sq,idq,ra) = pjq(query)
        self.assertEqual(iq[0][0],'chr6:1-10000000')
        self.assertEqual(rq[0]['rfilter'][0],"samples_count:5")
        self.assertEqual(sq[0],[])
        self.assertEqual(idq[0],[1,4])
       
    def test_range_query_parsing(self):
        '''tests the parsing of the string of ranges-as-filters constraints'''
        rfilters={}
        tests_ = [['samples_count',':',5],['coverage_sum','>:',3],['coverage_avg','<',5.5]]
        rfilters['rfilter']=["".join(map(lambda y: str(y),x)) for x in tests_]
        snaptron_ids = set()
        ranges_parsed = rqp(rfilters,snaptron_ids)
        #for col in ['samples_count','coverage_sum','coverage_avg']:
        for (col,op,val) in tests_:
            self.assertEqual(col in ranges_parsed,True)
            (op_,val_) = ranges_parsed[col]
            self.assertEqual(snapconfshared.operators[op],op_)
            self.assertEqual(val,val_)
   
    def test_basic_interval(self):
        '''make sure we're getting back an expected set of intropolis ids'''
        i = 0
        #get intropolis ids
        (iids,sids) = self.itc(IQs[i], filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]])
    
    def test_stream_output(self):
        '''make sure we're getting a correct header'''
        sout = StringIO()

        snaputil.REQ_FIELDS=[]
        snaputil.stream_header(sout,region_args=snaptron.default_region_args)
        hfields = sout.getvalue().split("\n")[0].rstrip().split("\t")
        self.assertEqual(len(hfields),len(snapconfshared.INTRON_HEADER_FIELDS)+1)

        req_field = 'snaptron_id'
        snaputil.REQ_FIELDS=[snapconfshared.INTRON_HEADER_FIELDS_MAP[req_field]]

        sout = StringIO()
        snaputil.stream_header(sout,region_args=snaptron.default_region_args)
        header = sout.getvalue().split("\n")[0].rstrip()
        self.assertEqual(header,'DataSource:Type\t%s' % (req_field))

    
    def test_basic_interval_and_range(self):
        '''make sure we're getting back an expected set of intropolis ids'''
        i = 0
        r = 0
        #get intropolis ids
        (iids,sids) = self.itc(IQs[i], range_query=RQs[r], filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs[r])])
    
    def test_basic_interval_and_range_and_ids(self):
        '''make sure we're getting back an expected set of intropolis ids'''
        i = 0
        r = 0
        d = 1
        #get intropolis ids
        (iids,sids) = self.itc(IQs[i], range_query=RQs[r], filter_set=IDs[d], filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs[r])+str(IDs[d])])
  
    def test_basic_gene_name_and_range(self):
        i = 1
        r = 1
        #get intropolis ids
        (iids,sids) = self.itc(IQs[i], range_query=RQs[r], rq=RQs_flat[r], filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs[r])])
    
    def test_basic_ids(self):
        '''make sure we're getting back an expected set of intropolis ids'''
        d = 0
        #get intropolis ids
        (iids,sids) = self.idc(IDs[d], filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[str(IDs[d])])



class TestQueryCalls(unittest.TestCase):
    '''
    Test the main top level methods in snaptron for querying with various predicates (regions, ranges, ids)
    These are full round trip tests (so not really unittests as such, more system/integration tests)
    '''

    def setUp(self):
        pass

    def process_query(self,input_):
        (iq,idq,rq,sq,ra) = pp(input_)
        return {'iq':iq,'rq':rq,'sq':sq,'idq':idq,'ra':ra}

    def test_interval_query(self):
        q = 0
        i = 0
        queries = self.process_query('regions=%s' % (IQs[i]))
        iq = queries['iq'][q]
        rq = ''
        (iids,sids) = qr([iq],rq,set(),filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]])
    
    def test_interval_query_for_ids(self):
        q = 0
        i = 0
        queries = self.process_query('regions=%s&fields=snaptron_id' % (IQs[i]))
        iq = queries['iq'][q]
        rq = ''
        (iids,sids) = qr([iq],rq,set(),filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]])
    
    def test_interval_with_range_query(self):
        q = 0
        i = 0
        r = 0
        queries = self.process_query('regions=%s&rfilter=%s' % (IQs[i],RQs_flat[r]))
        iq = queries['iq'][q]
        rq = queries['rq']
        (iids,sids) = qr([iq],rq,set(),filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs[r])])
         
    def test_interval_with_range_with_ids_query(self):
        q = 0
        i = 0
        r = 0
        d = 1
        queries = self.process_query('regions=%s&rfilter=%s&ids=%s' % (IQs[i],RQs_flat[r],",".join(IDs[d])))
        iq = queries['iq'][q]
        rq = queries['rq']
        snaptron_ids = set()
        qi(queries['idq'],snaptron_ids)
        (iids,sids) = qr([iq],rq,snaptron_ids,filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs[r])+str(IDs[d])])

    def test_interval_with_fp_ranges(self):
        q = 0
        i = 2
        r = 1
        queries = self.process_query('regions=%s&rfilter=%s&rfilter=%s' % (IQs[i],RQs_flat[r],RQs_flat[r+1]))
        iq = queries['iq'][q]
        rq = queries['rq']
        snaptron_ids = set()
        (iids,sids) = qr([iq],rq,snaptron_ids,filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs_flat[r])+str(RQs_flat[r+1])])
    
    def test_fp_ranges(self):
        q = 0
        i = 2
        r = 5
        queries = self.process_query('rfilter=%s,%s' % (RQs_flat[r],RQs_flat[r+1]))
        #queries = self.process_query('rfilter=samples_count:10000,coverage_avg>20')
        rq = queries['rq']
        snaptron_ids = set()
        ra = snaptron.default_region_args._replace(save_introns=True)
        #(iids,sids) = srl(rq,snaptron_ids,stream_back=False)
        (iids,sids) = srl(None,rq,snaptron_ids,region_args=ra)
        self.assertEqual(iids, EXPECTED_IIDS[str(RQs_flat[r])+str(RQs_flat[r+1])])
        #self.assertEqual(iids, set([1900915,17229066,14511883,18158500,19434757]))
    
    def test_interval_with_range_query_contains(self):
        q = 0
        i = 3
        r = 3
        queries = self.process_query('regions=%s&rfilter=%s&rfilter=%s&contains=1' % (IQs[i],RQs_flat[r],RQs_flat[r+1]))
        iq = queries['iq'][q]
        rq = queries['rq']
        (iids,sids) = qr([iq],rq,set(),filtering=True,region_args=queries['ra'])
        #snaptron.RETURN_ONLY_CONTAINED = False
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs_flat[r])+str(RQs_flat[r+1])])
    
    def test_interval_with_range_query_either_start(self):
        q = 0
        i = 5
        r = 3
        queries = self.process_query('regions=%s&rfilter=%s&rfilter=%s&either=1' % (IQs[i],RQs_flat[r],RQs_flat[r+1]))
        iq = queries['iq'][q]
        rq = queries['rq']
        (iids,sids) = qr([iq],rq,set(),filtering=True,region_args=queries['ra'])
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs_flat[r])+str(RQs_flat[r+1])])
    
    def test_interval_with_range_query_not_either_end(self):
        q = 0
        i = 4
        r = 3
        queries = self.process_query('regions=%s&rfilter=%s&rfilter=%s&either=2' % (IQs[i],RQs_flat[r],RQs_flat[r+1]))
        iq = queries['iq'][q]
        rq = queries['rq']
        (iids,sids) = qr([iq],rq,set(),filtering=True,region_args=queries['ra'])
        self.assertEqual(iids, set([]))
    
    def test_interval_with_range_query_exact(self):
        q = 0
        i = 5
        r = 3
        queries = self.process_query('regions=%s&rfilter=%s&rfilter=%s&exact=1' % (IQs[i],RQs_flat[r],RQs_flat[r+1]))
        iq = queries['iq'][q]
        rq = queries['rq']
        (iids,sids) = qr([iq],rq,set(),filtering=True,region_args=queries['ra'])
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i-1]+str(RQs_flat[r])+str(RQs_flat[r+1])])
    
    def test_interval_with_range_query_not_exact(self):
        q = 0
        i = 4
        r = 3
        queries = self.process_query('regions=%s&rfilter=%s&rfilter=%s&exact=1' % (IQs[i],RQs_flat[r],RQs_flat[r+1]))
        iq = queries['iq'][q]
        rq = queries['rq']
        (iids,sids) = qr([iq],rq,set(),filtering=True,region_args=queries['ra'])
        self.assertEqual(iids, set([]))

class TestSampleSearch(unittest.TestCase):
    '''
    Test the search and recovery of sample IDs and coverages in a junction's sample/coverage list
    '''

    def setUp(self):
        pass

    def test_basic_extraction(self):
        sample_ids = set(["1","5","53","276","4987","18000"])
        sid_search_obj = snquery.build_sid_ahoc_queries(sample_ids)
        samples_str = ",5:5,4:32,276:7,18000:276"
        fields = range(0,snapconfshared.SAMPLE_IDS_COL+5)
        fields[snapconfshared.SAMPLE_IDS_COL] = samples_str
        sid_search_iter = sid_search_obj.iter(samples_str)
        (found,fields) = snaputil.extract_sids_and_covs_from_search_iter(sid_search_iter, fields)
        samples = set([5,276,18000])
        covs = set([5,7,276])
        samples_found = set(found[0:len(found),0])
        covs_found = set(found[0:len(found),1])
        self.assertEqual(len(samples.intersection(samples_found)), len(samples))
        self.assertEqual(len(covs.intersection(covs_found)), len(covs))
    
    def test_summary_recalculation(self):
        sample_ids = set(["1","5","53","276","4987","18000"])
        sid_search_obj = snquery.build_sid_ahoc_queries(sample_ids)
        samples_str = ",5:5,4:32,276:7,18000:276"
        sids_covs_should_be_found = set(["5:5","276:7","18000:276"])
        fields = range(0,snapconfshared.SAMPLE_IDS_COL+5)
        fields[snapconfshared.SAMPLE_IDS_COL+1] = 4
        fields[snapconfshared.SAMPLE_IDS_COL+2] = 320
        fields[snapconfshared.SAMPLE_IDS_COL+3] = 80
        fields[snapconfshared.SAMPLE_IDS_COL+4] = 19.5
        fields[snapconfshared.SAMPLE_IDS_COL] = samples_str
        sid_search_iter = sid_search_obj.iter(samples_str)
        (found,fields) = snaputil.extract_sids_and_covs_from_search_iter(sid_search_iter, fields)
        sids_covs_from_search = set([x for x in fields[snapconfshared.SAMPLE_IDS_COL].split(",")])
        sids_covs_from_search.remove('')
        self.assertEqual(sids_covs_from_search, sids_covs_should_be_found)
        self.assertEqual(fields[snapconfshared.SAMPLE_IDS_COL+1], 3)
        self.assertEqual(fields[snapconfshared.SAMPLE_IDS_COL+2], 288)
        self.assertEqual(fields[snapconfshared.SAMPLE_IDS_COL+3], 96)
        self.assertEqual(fields[snapconfshared.SAMPLE_IDS_COL+4], 7)
    
    def test_range_filter(self):
        sample_ids = set(["1","5","53","276","4987","18000"])
        sid_search_obj = snquery.build_sid_ahoc_queries(sample_ids)
        samples_str = ",5:5,4:32,276:7,18000:276"
        fields = range(0,snapconfshared.SAMPLE_IDS_COL+5)
        fields[snapconfshared.SAMPLE_IDS_COL+1] = 4
        fields[snapconfshared.SAMPLE_IDS_COL+2] = 320
        fields[snapconfshared.SAMPLE_IDS_COL+3] = 80
        fields[snapconfshared.SAMPLE_IDS_COL+4] = 19.5
        fields[snapconfshared.SAMPLE_IDS_COL] = samples_str
        sid_search_iter = sid_search_obj.iter(samples_str)
        (found,fields) = snaputil.extract_sids_and_covs_from_search_iter(sid_search_iter, fields)
        range_filters = {'samples_count':[operator.gt,2],'coverage_sum':[operator.eq,288],'coverage_avg':[operator.ge,3.0],'coverage_median':[operator.lt,20]}
        self.assertEqual(snaputil.filter_by_ranges(fields, range_filters), False)
        #change range_filters
        range_filters = {'samples_count':[operator.gt,2],'coverage_sum':[operator.eq,288],'coverage_avg':[operator.ge,3.0],'coverage_median':[operator.ne,7.0]}
        self.assertEqual(snaputil.filter_by_ranges(fields, range_filters), True)

if __name__ == '__main__':
    unittest.main()
