#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <string.h>
#include <unistd.h>
#include <string.h>
#include <cstdlib>
#include <vector>

#include <unordered_map>
template<typename K, typename V>
using hash_map = std::unordered_map<K,V>;

typedef hash_map<std::string, bool> strset;
typedef hash_map<std::string, uint32_t> strint;

int MAX_SID_LENGTH = 50;

int main(int argc, char* argv[]) 
{
	int o;
	std::string samples_md_file;
    uint32_t num_samples = 0;
    int region_buffer_size = 1024;
	while((o  = getopt(argc, argv, "s:n:")) != -1)
    {
		switch(o) 
		{
			case 's': samples_md_file = optarg; break;
			case 'n': num_samples = atoi(optarg); break;
		}
	}
    FILE* fin = fopen(samples_md_file.c_str(), "r");

    strint samples;
    char* sids = new char[num_samples*MAX_SID_LENGTH];
    char* buf = sids;
	size_t length = -1;
    int i = 0;
    //for dumping the rest of the line
	size_t length2 = 20048576;
    char* largebuf = new char[length2];
    //dump header first
    char delim = '\t';
	ssize_t bytes_read = getline(&buf, &length, fin);
	bytes_read = getdelim(&buf, &length, delim, fin);
    uint32_t sidx = 0;
	while(bytes_read != -1) 
    {
        //replace tab with null for terminator
        sids[i+(bytes_read-1)] = '\0';
        samples[&(sids[i])] = sidx++;
        i += bytes_read;
        buf = &(sids[i]);
        //read rest of line and dump
	    bytes_read = getline(&largebuf, &length2, fin);
		bytes_read = getdelim(&buf, &length, delim, fin);
    }
    fclose(fin);
    //fprintf(stderr,"num samples %lu\n",samples.size());
    fprintf(stdout,"rail_id\tjunction_count\tjunction_coverage\tjunction_avg_coverage\n");
    uint64_t* counts = new uint64_t[num_samples];
    uint64_t* coverages = new uint64_t[num_samples];
    buf = largebuf;
    length = -1;
    //first comma
	bytes_read = getdelim(&buf, &length, ',', stdin);
    //now first sample:coverage
	bytes_read = getdelim(&buf, &length, ',', stdin);
    uint64_t cov = 0;
    delim = ',';
    char tuple_delim = ':';
    char* tok;
    while(bytes_read != -1)
    {
        //1st token is sample ID
	    tok = strtok(buf, &tuple_delim);
        //get the sample index into the counting arrays
        uint32_t sidx = samples[tok];
        //2nd token is coverage
	    tok = strtok(NULL, &tuple_delim);
        cov = atol(tok);
        counts[sidx]++;
        coverages[sidx] += cov;
        //get the next tuple
	    bytes_read = getdelim(&buf, &length, delim, stdin);
        while(buf[0] == '\n' || buf[0] == ',')
	        bytes_read = getdelim(&buf, &length, delim, stdin);
    }
    for(auto itr = samples.begin(); itr != samples.end(); ++itr)
    {
        uint64_t count = counts[itr->second];
        uint64_t cov = coverages[itr->second];
        //fprintf(stdout,"%s\t%lu\t%lu\t%.12f\n",itr->first.c_str(), count, cov, double (count/(double)cov));
        fprintf(stdout,"%s\t%lu\t%lu\t%.12f\n",itr->first.c_str(), count, cov, cov / (double)count);
    }
}
