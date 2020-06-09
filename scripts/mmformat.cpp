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

//efficient Snaptron formatted junction2Matrix Market format converter (only)

//input format example row:
//chr1    3000045 3017777 +   ,1910616:1,3818268:1,3825783:1,3871447:1,967629:1,969806:1

int LINE_COUNT_PRINT = 100000;

//1-base
int samples_column = 11;
int bytes_per_sample_field = 26;
//store everything but samples:coverrages
int extra_field_bytes = 2048;

using namespace std;

typedef vector<uint64_t> vec64;

void process_line(char* buf, uint32_t line_start_idx, uint32_t sample_col_idx, uint32_t sample_col_end_idx, char* prefix_buf, char* samples_buf, char delim, uint64_t* row_idx, uint32_t* sample_id_map, uint64_t* num_non0s, FILE* fout)
{
    (*row_idx)++;
    //print prefix
    //temporariy replace tab with null to print
    buf[sample_col_idx] = '\0';
    //fprintf(stderr,"sample_col_idx b4 coord print: %u\n",sample_col_idx);
    //just print the whole coordinate + anotation prefix for now
    //TODO: cut out only the coordinate columns we want for the prefix
    fprintf(stdout,"%s\n",&(buf[line_start_idx]));
    buf[sample_col_idx] = delim;

    //do samples search
    char sample_col_end_idx_char = buf[sample_col_end_idx];
    buf[sample_col_end_idx]='\0';
    uint32_t sample_count = 0;
    int i = sample_col_idx;
    //offsets from the first sample's ','
    int sid_start_pos = sample_col_idx+2;
    int cov_start_pos = sid_start_pos+3;
    //go to end of samples/coverages, skip rest of line (dont need it)
    while(buf[i] != '\0')
    {
        if(buf[i] == ',' && i != sample_col_idx+1)
        {
            //track number of total row/column pairs (with > 0 value)
            (*num_non0s)++;
            sample_count++;
            buf[cov_start_pos-1] = '\0';
            uint32_t sample_id = atol(&(buf[sid_start_pos]));
            buf[cov_start_pos-1] = ':';
            sid_start_pos = i + 1;
            uint64_t col_idx = sample_id_map[sample_id];
            buf[i] = '\0';
            uint32_t cov = atol(&(buf[cov_start_pos]));
            buf[i] = ',';
            fprintf(fout,"%lu\t%lu\t%u\n",*row_idx,col_idx,cov);
        }
        if(buf[i] == ':')
            cov_start_pos = i+1;
        i++;
    }
    if(i != sample_col_idx+1)
    {
        (*num_non0s)++;
        sample_count++;
        buf[cov_start_pos-1] = '\0';
        uint32_t sample_id = atol(&(buf[sid_start_pos]));
        buf[cov_start_pos-1] = ':';
        uint64_t col_idx = sample_id_map[sample_id];
        buf[i] = '\0';
        uint32_t cov = atol(&(buf[cov_start_pos]));
        buf[i] = ',';
        fprintf(fout,"%lu\t%lu\t%u\n",*row_idx,col_idx,cov);
    }
    buf[sample_col_end_idx]=sample_col_end_idx_char;
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
  
    FILE* fin = fopen(sample_ids_file.c_str(),"r");
    char* fname = new char[1024];
    sprintf(fname, "%s.mm", output_file.c_str());
    FILE* fout = fopen(fname,"wb");
     
    size_t length = -1;
    uint32_t read_size = (max_num_samples*bytes_per_sample_field)+extra_field_bytes;
    char* buf = new char[2*read_size];
    //temp storage for single sample ID (rid)
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
        bytes_read = getline(&buf, &length, fin);
    }
    fclose(fin);
    fprintf(stderr,"num samples to filter for %d, largest sample_id: %lu, input buf size: %u\n",num_samples, largest_sample_id, 2*read_size);
     
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
    

    //TODO: code top off to end of current line
    uint32_t sample_col_idx = -1;
    uint32_t sample_col_end_idx = -1;
    uint32_t last_line_end_idx = -1;
    //index within line
    uint32_t line_len = 0;
    uint64_t total_lines = 0;
    //1 base rows
    uint64_t row_idx = 0;
    uint64_t num_non0s = 0;
    //print headers
    fprintf(stdout,"chromosome	start	end	length	strand	annotated	left_motif	right_motif	left_annotated	right_annotated\n");
    char* header = new char[1024];
    int header_len_original = 49;
    sprintf(header, "%%%%MatrixMarket matrix coordinate integer general\n");
    //pad out header line to allow writing 2nd #rows,#columns,#non0s at end
    //40 is maximum number of characters in new line, assuming up to 12 chars per number
    int header_len_w_padding = header_len_original + 40;
    header[header_len_original]='%';
    for(j = header_len_original+1; j < header_len_w_padding-1; j++)
        header[j]=' ';
    header[j]='\n';
    fprintf(fout, "%s", header);
   
    uint64_t i = 0;
    uint64_t total_bytes = 0;
    bytes_read = fread(buf, 1, read_size, stdin);
    bytes_read += read_to_end_of_line(stdin, &(buf[bytes_read]));
    
    uint64_t line_count = 0;
    uint64_t field_count = 1;
    //fprintf(stdout, "bytes read %d\n", bytes_read);
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
                    sample_col_idx = i;
                else if(field_count == (samples_column + 1))
                    sample_col_end_idx = i;
            }
            else if(buf[i] == '\n')
            {
                if(sample_col_end_idx == -1)
                    sample_col_end_idx = i;
                total_lines++;
                if(total_lines % LINE_COUNT_PRINT == 0)
                    fprintf(stderr,"lines_processed:%lu\n",total_lines);
                process_line(buf, last_line_end_idx+1, sample_col_idx, sample_col_end_idx, prefix_buf, samples_buf, output_delim, &row_idx, sample_id_map, &num_non0s, fout); 
                last_line_end_idx = i;
                sample_col_idx = -1;
                sample_col_end_idx = -1;
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
