#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <string.h>
#include <unistd.h>
#include <cstdlib>
#include <vector>
#include <algorithm>
typedef std::vector<uint64_t> vecint;

int MAX_SID_LENGTH = 50;
//999 billion for a single junction in a single sample is high, but just in case
int MAX_COV_LENGTH=11;

int main(int argc, char* argv[]) 
{
	int o;
	std::string samples_md_file;
    //total number of samples
    uint32_t num_samples = 0;
	while((o  = getopt(argc, argv, "s:n:")) != -1)
    {
		switch(o) 
		{
			case 's': samples_md_file = optarg; break;
			case 'n': num_samples = atoi(optarg); break;
		}
	}
    FILE* fin = fopen(samples_md_file.c_str(), "r");

    uint64_t* sids = new uint64_t[num_samples];
    //enough for all coverages for all samples and the delimiters for a single input line
    //but we'll also use it for reading in the sample IDs which are way smaller
    char* inputbuf = new char[(num_samples*(MAX_COV_LENGTH+1))+1];
    char* buf = inputbuf;
	size_t length = -1;
    int i = 0;
    //dump header first
	ssize_t bytes_read = getline(&buf, &length, fin);
    uint32_t sidx = 0;
	while(bytes_read != -1) 
    {
        //replace tab with null for terminator
        sids[sidx++] = strtoull(buf,nullptr,0);
        //read rest of line and dump
	    bytes_read = getline(&buf, &length, fin);
    }
    fclose(fin);
    fprintf(stderr,"num samples %u\n", sidx);
    
    //large enough array for all samples with >= 1 coverage plus: ids, ',' and ':', and a terminating char
    //doesn't need to be init'd, we'll just write over whatever's there
    char* outstr = new char[(num_samples*(MAX_SID_LENGTH+MAX_COV_LENGTH+2))+1];
    //keep a vector of the coverages for a line, used to sort and get median
    vecint covs;
    buf = inputbuf;
    length = -1;
    int bytes_printed = 0;
    char* tok = nullptr; 
    int fidx = 0;
    int oidx = 0;
    uint64_t sample_coverage = 0;
    uint64_t coverage_sum = 0;
    uint64_t coverage_count = 0;
    char delim = '\t';
	bytes_read = getline(&buf, &length, stdin);
    while(bytes_read != -1)
    {
        fidx = 0;
        oidx = 0;
        sample_coverage = 0;
        coverage_sum = 0;
        coverage_count = 0;
        covs.clear();
	    
        tok = strtok(buf, &delim);
        while(fidx < sidx && tok != nullptr)
        {
            fidx++;
            //fprintf(stderr,"%s\n",tok);
            sample_coverage = strtoull(tok,nullptr,0);
            //if(strcmp(tok,"0") == 0)
            if(sample_coverage == 0)
            {
                tok = strtok(NULL, &delim);
                continue;
            }
            coverage_sum += sample_coverage;
            coverage_count++;
            uint32_t sid = sids[fidx-1];
            //output string for sid:coverage string with delimiters
            bytes_printed = sprintf(&(outstr[oidx]),",%u:%lu",sid,sample_coverage);
            oidx += bytes_printed;
            covs.push_back(sample_coverage);
            tok = strtok(NULL, &delim);
        }
        if(coverage_count > 0)
        {
            std::sort(covs.begin(), covs.end());
            int median_idx = ceil(coverage_count / 2);
            double median = 0.0;
            median = covs[median_idx];
            if(coverage_count % 2 == 0)
                median = (covs[median_idx] + covs[median_idx+1])/2;
            double avg = coverage_sum / coverage_count;
            outstr[oidx]='\0';
            fprintf(stdout,"%s\t%lu\t%lu\t%0.3f\t%0.3f\n", outstr, coverage_count, coverage_sum, avg, median);
        }
        else
            fprintf(stdout,"SKIP\n");
	    bytes_read = getline(&buf, &length, stdin);
    }
    fprintf(stderr,"DONE\n");
}
