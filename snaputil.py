#!/usr/bin/env python
import os
import cPickle

def load_cpickle_file(filepath):
    ds = None
    if os.path.exists(filepath):
        with open(filepath,"rb") as f:
            ds=cPickle.load(f)
    return ds

def store_cpickle_file(filepath,ds):
    if not os.path.exists(filepath):
        with open(filepath,"wb") as f:
            cPickle.dump(ds,f,cPickle.HIGHEST_PROTOCOL)
        return True
    return False

def retrieve_from_db_by_ids(dbh,select,ids):
    wheres = ['?' for x in ids]
    select = "%s (%s);" % (select,','.join(wheres))
    ids_ = [int(id_) for id_ in ids]
    return dbh.execute(select,ids_)
