#!/usr/bin/env python2.7
import sys
import os
import unittest

import snapconf
import snaputil
import snaptron

#set of test interval queries
IQs=['chr1:10160-10161','CD99']
#RQs=['1:100000-100000','1:5-5']
#IRQs are a set of combination of indexes from IQs and RQs
RQs=[{'length':[snapconf.operators['='],54]},{'samples_count':[snapconf.operators['='],10]}]
IDs=[set(['33401689','33401829']),set(['6','9'])]
#holds the set of intropolis ids for each specific query for the original SRA set of inropolis junctions
EXPECTED_IIDS={
               IQs[0]:set(['0','1','2','3','4','5','6','9','10','11','13','14','15','16','17','18','20','21','22','23','24','26','27','28','29','30','31','32','33','34','35','36','37','38']),
               IQs[0]+str(RQs[0]):set(['0','6','9']),
               IQs[0]+str(RQs[0])+str(IDs[1]):set(['6','9']),
               str(IDs[0]):set(['33401689','33401829']),
               IQs[1]+str(RQs[1]):set(['41341710','41341711','41341836','41342617','41343142','41343152','41343193','42691062','42691119','42691141','42691142'])
              }

def setUpModule():
    pass

def tearDownModule():
    pass

#shortcuts for snaptron methods used in tests
tc = snaptron.run_tabix
rqp = snaptron.range_query_parser
sbi = snaptron.search_introns_by_ids
sbg = snaptron.search_by_gene_name

tdbs = snapconf.TABIX_DBS

class TestTabixCalls(unittest.TestCase):
    '''
    check tabix for basic queries (both interval and range including ids)
    def run_tabix(qargs,rquerys,tabix_db,filter_set=None,sample_set=None,filtering=False,print_header=True,debug=True):
    returns an id set if filtering==True
    can also populate sample_set if defined
    '''

    def setUp(self):
        pass
   
    def itc(self,interval_query,range_query=None,filter_set=None,sample_set=None,filtering=False):
        '''wrap the normal run_tabix/search_by_gene_name call to hardcode defaults for interval/gene name querying'''
        if snapconf.INTERVAL_PATTERN.search(interval_query): 
            return tc(interval_query,range_query,tdbs['chromosome'],intron_filters=filter_set,sample_filters=sample_set,save_introns=filtering)
        return sbg(interval_query,range_query,intron_filters=filter_set,save_introns=filtering) 
    
    def idc(self,ids,filtering=False):
        '''wrap the normal run_tabix call to hardcode defaults for interval querying AND range filtering'''
        return sbi(ids,None,filtering=filtering)
    
    def idcr(self,ids,range_query):
        '''wrap the normal run_tabix call to hardcode defaults for interval querying AND range filtering'''
        return sbi(ids,range_query)
    

#actual tests 
    def test_basic_interval(self):
        '''make sure we're getting back an expected set of intropolis ids'''
        i = 0
        #get intropolis ids
        (iids,sids) = self.itc(IQs[i], filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]])
    
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
        (iids,sids) = self.itc(IQs[i], RQs[r], filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[IQs[i]+str(RQs[r])])
    
    def test_basic_ids(self):
        '''make sure we're getting back an expected set of intropolis ids'''
        d = 0
        #get intropolis ids
        iids = self.idc(IDs[d], filtering=True)
        self.assertEqual(iids, EXPECTED_IIDS[str(IDs[d])])
    
if __name__ == '__main__':
    unittest.main()
               
#RQs[0]:set(["1042183","4655249","8228366","8228479","8613428","8813669","8992620","9191837","9191838","12439314","16533047","16585013","17895417","19061596","19061599","19659394","20360595","20360638","20360704","20360763","20360865","23543324","23821668","25640534","25640535","26783371","28153140","28463313","31138498","31576775","32888166","32888167","35125664","37187404","37876025","37876029","38244820","38418223","42053224"])
