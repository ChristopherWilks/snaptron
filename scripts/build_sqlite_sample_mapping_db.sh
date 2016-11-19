#!/bin/bash

sqlite3 ${1}.sqlite "CREATE TABLE by_sample_id (sample_id INTEGER NOT NULL,snaptron_ids TEXT NOT NULL,PRIMARY KEY (sample_id));"

bzcat ${2} > /data/import &
sqlite3 ${1}.sqlite -cmd '.separator "\t"' ".import /data/import by_sample_id"
