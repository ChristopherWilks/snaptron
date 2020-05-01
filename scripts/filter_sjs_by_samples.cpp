#include <iostream>
#include <sstream>
#include <fstream>
#include <memory>
#include <array>
#include <string>
#include <vector>
#include <string.h>
#include <unistd.h>
#include <cstdlib>
#include "aho_corasick.hpp"

//efficient Snaptron formatted junction filter
//currently supports filtering by:
//1) list of >=1 sample_ids, list format: ",sample_id:"

//supports read from either junctions.bgz or sqlite3 
//(faster since uncompressed)

//1-base
int samples_column = 12;
int bytes_per_sample_field = 26;
//store everything but samples:coverrages
int extra_field_bytes = 2048;

namespace ac = aho_corasick;
using trie = ac::trie;

using namespace std;

void process_line(char* buf, uint32_t line_len, uint32_t sample_col_idx, uint32_t sample_col_end_idx, trie* sample_search, char* prefix_buf, char* samples_buf, char delim)
{
    //do samples search
    buf[sample_col_end_idx+1]='\0';
    char* buf_ptr_start_samples = &(buf[sample_col_idx]);
    auto sample_tokens = sample_search->tokenise(string(buf_ptr_start_samples));
    bool matching = false;

    //loop through the tokens and get those which match (if any)
    //and their coverages
    uint32_t buf_pos = sample_col_idx;
    uint32_t sample_buf_pos = 0;
    uint32_t sample_count = 0;
    uint64_t sample_cov_sum = 0;
    for(const auto& str_frag : sample_tokens)
    {
        if(str_frag.is_match())
        {
            matching = true;
            sample_count++;
            //only want to include the samples and coverages which are in the list, in the output
            //auto sample_id = str_frag.get_fragment();
            int start_pos = str_frag.get_emit().get_start();
            //copy" ,sample_id:coverage" value into sample buffer
            samples_buf[sample_buf_pos++] = ',';
            buf_pos = start_pos + 1;
            int cov_start_pos = 0;
            while(buf_ptr_start_samples[buf_pos] != ',' && buf_ptr_start_samples[buf_pos] != '\0')
            {
                if(buf_ptr_start_samples[buf_pos] == ':')
                    cov_start_pos = sample_buf_pos+1;
                samples_buf[sample_buf_pos++] = buf_ptr_start_samples[buf_pos++];
            }
            //add to running total of coverage
            char temp = samples_buf[sample_buf_pos];
            samples_buf[sample_buf_pos] = '\0';
            sample_cov_sum += atol(&(samples_buf[cov_start_pos]));
            samples_buf[sample_buf_pos] = temp;
        }
    }

    if(!matching)
        return;

    samples_buf[sample_buf_pos] = '\0';
    //process prefix
    //if matching, print prefix
    //temporariy replace tab with null to print
    buf[sample_col_idx-1] = '\0';
    fprintf(stdout,"%s",buf);
    buf[sample_col_idx-1] = delim;
    fprintf(stdout,"%c%s%c%u%c%lu\n", delim, samples_buf, delim, sample_count, delim, sample_cov_sum);
}

ssize_t read_to_end_of_line(FILE* fin, char* buf)
{
    int i = 0;
    char c = getc(fin);
    while(c != EOF)
    {
        buf[i++] = c;
        if(c == '\n')
            break;
        c = getc(fin);
    }
    return i;
}


int main(int argc, char** argv)
{
	int o;
	std::string sample_ids_file;
    uint32_t max_num_samples = 0;
    char input_delim = '\t';
    char output_delim = '\t';
	while((o  = getopt(argc, argv, "s:d:o:n:")) != -1) 
    {
		switch(o) 
		{
			case 's': sample_ids_file = optarg; break;
			case 'd': input_delim = optarg[0]; break;
			case 'o': output_delim = optarg[0]; break;
			case 'n': max_num_samples = atol(optarg); break;
        }
    }
	if(sample_ids_file.length() == 0 || max_num_samples == 0) 
    {
		std::cerr << "You must pass a filename containing the list of sample_ids to filter for (-s) and the total number of samples in the entire compilation (-n)\n";
		exit(-1);
	}
   
    trie sample_search; 
    FILE* fin = fopen(sample_ids_file.c_str(),"r");
     
	size_t length = -1;
    uint32_t read_size = (max_num_samples*bytes_per_sample_field)+extra_field_bytes;
    char* buf = new char[2*read_size];
    uint32_t num_samples = 0;
    //expects sample_id format to be: ",sample_id:"
    ssize_t bytes_read = getline(&buf, &length, fin);
	while(bytes_read != -1)
    {
        num_samples++;
        //overwrite newline
        buf[bytes_read-1] = '\0';
        sample_search.insert(string(strdup(buf)));
        bytes_read = getline(&buf, &length, fin);
    }
    fclose(fin);
    fprintf(stderr,"num samples to filter for %d\n",num_samples);
       
    char* prefix_buf = new char[extra_field_bytes];
    char* samples_buf = new char[read_size];
    
    uint64_t line_count = 0;
    uint64_t field_count = 1;

    uint64_t i = 0;
    uint64_t total_bytes = 0;
    bytes_read = fread(buf, 1, read_size, stdin);
    bytes_read += read_to_end_of_line(stdin, &(buf[bytes_read]));
    //TODO: code top off to end of current line
    uint32_t sample_col_idx = 0;
    uint32_t sample_col_end_idx = 0;
    uint32_t last_line_end_idx = -1;
    //index within line
    uint32_t line_len = 0;
    while(bytes_read > 0)
    {
        total_bytes += bytes_read;
        fprintf(stderr,"total_bytes_read:%lu\n",total_bytes);
        while(i < bytes_read)
        {
            if(buf[i] == input_delim)
            {
                buf[i] = output_delim;
                field_count++;
                if(field_count == samples_column)
                    sample_col_idx = line_len + 1;
                else if(field_count == (samples_column + 1))
                    sample_col_end_idx = line_len - 1;
            }
            else if(buf[i] == '\n')
            {
                process_line(&(buf[last_line_end_idx+1]), line_len, sample_col_idx, sample_col_end_idx, &sample_search, prefix_buf, samples_buf, output_delim); 
                last_line_end_idx = i;
                sample_col_idx = 0;
                sample_col_end_idx = 0;
                field_count = 1;
                line_len = -1;
                line_count++;
            }
            i++;
            line_len++;
        }
        bytes_read = fread(buf, 1, read_size, stdin);
        bytes_read += read_to_end_of_line(stdin, &(buf[bytes_read]));
        i = 0;
        last_line_end_idx = -1;
    }
    total_bytes += bytes_read;
    fprintf(stderr,"total_bytes_read:%lu\n",total_bytes);
    fprintf(stderr,"DONE\n");
}
