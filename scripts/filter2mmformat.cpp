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

/* This file is part of Snaptron.

 Snaptron is free software: you can redistribute it and/or modify
 it under the terms of the 

    The MIT License

    Copyright (c) 2016-  by Christopher Wilks <broadsword@gmail.com> 
                         and Ben Langmead <langmea@cs.jhu.edu>

    Permission is hereby granted, free of charge, to any person obtaining
    a copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
    BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
    ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
*/

//efficient Snaptron formatted junction2Matrix Market format filter/converter
//currently supports filtering by:
//1) list of >=1 sample_ids, list format: "sample_id" (no ',' or ':'s)

//supports read from either junctions.bgz or sqlite3 
//(faster since uncompressed)

int LINE_COUNT_PRINT = 100000;

//1-base
int samples_column = 12;
int bytes_per_sample_field = 26;
//store everything but samples:coverrages
int extra_field_bytes = 2048;

namespace ac = aho_corasick;
using trie = ac::trie;


using namespace std;

typedef vector<uint64_t> vec64;

void process_line(char* buf, uint32_t line_len, uint32_t sample_col_idx, uint32_t sample_col_end_idx, trie* sample_search, char* prefix_buf, char* samples_buf, char delim, uint64_t* row_idx, uint32_t* sample_id_map, uint64_t* num_non0s, FILE* fout)
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
            if(!matching)
            {
                (*row_idx)++;
                //process prefix
                //if matching, print prefix
                //temporariy replace tab with null to print
                buf[sample_col_idx-1] = '\0';
                //just print the whole coordinate + anotation prefix for now
                //TODO: cut out only the coordinate columns we want for the prefix
                fprintf(stdout,"%s\n",buf);
                buf[sample_col_idx-1] = delim;
                matching = true;
            }
            //track number of total row/column pairs (with > 0 value)
            (*num_non0s)++;
            sample_count++;
            //only want to include the samples and coverages which are in the list, in the output
            int start_pos = str_frag.get_emit().get_start();
            buf_pos = start_pos + 1;
            int sample_id_start_pos = buf_pos;
            int cov_start_pos = 0;
            while(buf_ptr_start_samples[buf_pos] != ',' && buf_ptr_start_samples[buf_pos] != '\0')
            {
                if(buf_ptr_start_samples[buf_pos] == ':')
                    cov_start_pos = buf_pos+1;
                buf_pos++;
            }
            //add to running total of coverage
            buf[cov_start_pos-1] = '\0';
            uint32_t sample_id = atol(&(buf_ptr_start_samples[sample_id_start_pos]));
            buf[cov_start_pos-1] = ':';
            uint64_t col_idx = sample_id_map[sample_id];
            char eol = buf_ptr_start_samples[buf_pos];
            buf_ptr_start_samples[buf_pos] = '\0';
            uint32_t cov = atol(&(buf_ptr_start_samples[cov_start_pos]));
            fprintf(fout,"%lu\t%lu\t%u\n",*row_idx,col_idx,cov);
        }
    }
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
	std::string output_file;
    uint32_t max_num_samples = 0;
    char input_delim = '\t';
    char output_delim = '\t';
	while((o  = getopt(argc, argv, "s:d:p:n:f:")) != -1) 
    {
		switch(o) 
		{
            //sample_ids_file should be sorted in the order that sample columns are expected in the sparse matrix format
			case 's': sample_ids_file = optarg; break;
			case 'd': input_delim = optarg[0]; break;
			case 'p': output_file = optarg; break;
			case 'n': max_num_samples = atol(optarg); break;
        }
    }
	if(sample_ids_file.length() == 0 || max_num_samples == 0 || output_file.length() == 0) 
    {
		std::cerr << "You must pass a filename containing the list of sample_ids to filter for (-s) and the total number of samples in the entire compilation (-n) and the output filename prefix (-p)\n";
		exit(-1);
	}
  
    trie sample_search; 
    FILE* fin = fopen(sample_ids_file.c_str(),"r");
    char* fname = new char[1024];
    sprintf(fname, "%s.mm", output_file.c_str());
    FILE* fout = fopen(fname,"wb");
     
	size_t length = -1;
    uint32_t read_size = (max_num_samples*bytes_per_sample_field)+extra_field_bytes;
    char* buf = new char[2*read_size];
    //temp storage for single sample ID (rid)
    char* sample_id_buf = new char[1024];
    sample_id_buf[0] = ',';
    uint32_t num_samples = 0;
    //expects sample_id format to be: ",sample_id:"
    ssize_t bytes_read = getline(&buf, &length, fin);
    uint64_t largest_sample_id = 0;
    uint64_t sample_id = 0;
    vec64 sample_ids;
	while(bytes_read != -1)
    {
        num_samples++;
        //overwrite newline
        buf[bytes_read-1] = '\0';
        sample_id = atol(buf);
        sample_ids.push_back(sample_id);
        if(sample_id > largest_sample_id)
            largest_sample_id = sample_id;
        strcpy(&(sample_id_buf[1]), buf);
        sample_id_buf[bytes_read] = ':';
        sample_id_buf[bytes_read+1] = '\0';
        sample_search.insert(string(strdup(sample_id_buf)));
        bytes_read = getline(&buf, &length, fin);
    }
    fclose(fin);
    fprintf(stderr,"num samples to filter for %d, largest sample_id: %lu\n",num_samples, largest_sample_id);
     
    //use this to quickly map from the sample_id to the column position for the 
    //sparse matrix format 
    uint32_t* sample_id_map = new uint32_t[largest_sample_id];
    uint32_t j;
    for(j = 0; j < sample_ids.size(); j++)
    {
        //start at 1 for j column indices in sparse matrix file
        sample_id_map[sample_ids[j]] = j+1;
    }

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
    uint64_t total_lines = 0;
    //1 base rows
    uint64_t row_idx = 0;
    uint64_t num_non0s = 0;
    //print headers
    //jxs header is just the first 11 columns of the snaptron format
    fprintf(stdout,"snaptron_id	chromosome	start	end	length	strand	annotated	left_motif	right_motif	left_annotated	right_annotated	samples	samples_count	coverage_sum	coverage_avg	coverage_median	source_dataset_id\n");
    char* header = new char[1024];
    int header_len_original = 49;
    sprintf(header, "%%%%MatrixMarket matrix coordinate integer general\n");
    //pad out header line to allow writing 2nd #rows,#columns,#non0s at end
    //40 is maximum number of characters in new line, assuming up to 12 chars per number
    int header_len_w_padding = header_len_original + 40;
    header[header_len_original]='%';
    for(j = header_len_original+1; j < header_len_w_padding-1; j++)
        header[j]='0';
    header[j]='\n';
    fprintf(fout, "%s", header);
    while(bytes_read > 0)
    {
        total_bytes += bytes_read;
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
                total_lines++;
                if(total_lines % LINE_COUNT_PRINT == 0)
                    fprintf(stderr, "lines read:%lu\n",total_lines);
                process_line(&(buf[last_line_end_idx+1]), line_len, sample_col_idx, sample_col_end_idx, &sample_search, prefix_buf, samples_buf, output_delim, &row_idx, sample_id_map, &num_non0s, fout); 
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
    //now go back and update the last header line with numbers
    sprintf(header,"\n%lu\t%u\t%lu\n", row_idx, num_samples, num_non0s);
    int header_len = strlen(header);
    int offset = header_len_w_padding - header_len;
    fseek(fout, offset, SEEK_SET);
    fprintf(fout, "%s", header);
    fclose(fout);

    total_bytes += bytes_read;
    fprintf(stderr,"total_bytes_read:%lu\n",total_bytes);
    fprintf(stderr,"DONE\n");
}
