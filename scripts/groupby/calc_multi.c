#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <stdint.h>
#include <stdbool.h>

//follows numpy convention,
//assuming 2-dim matrix, row operations
//summarizes across all rows, (#lines == 1, #columns = original input)
//while column operations summarize across the columns (#lines == #rows, #columns == 1)
int ROW_AXIS=0;
int COL_AXIS=1;

typedef struct config_def {
	int bp_col;
	int chrm_col;
	int start_col;
	int end_col;
	int base_col_start;
	int axis;
	char* op;
	char* label;
    int filter;
} config_settings;

//tokenize each line to get the coordinates and the list of sample counts
//if doing a axis=COLUMN computation do it per row here
int process_line(int first, char* line, char* delim, double** vals, double** vals2, config_settings config_def, int print_coord, double* total_sum, uint64_t* ilen)
{
	char* line_copy = strdup(line);
	char* tok = strtok(line_copy, delim);
	int i = 0;
	char* chrm;
	long start, end;
	int static_idx = config_def.base_col_start;
	//int* col_idx = &static_idx;
	//if(config_def.axis == ROW_AXIS)
		//col_idx = &i;
	int* col_idx = &i;
    int col_idx_real = 0;
    double sum = 0;
	while(tok != NULL)
	{
		//if first line, only loop through to get
		//count of fields, this will be used to create
		//the actual storage array for the counts in a 2nd pass
		//through (only this line)
		if(first)
		{
			i++;
			tok = strtok(NULL,delim);
			continue;
		}
		if(i == config_def.chrm_col)
			chrm=strdup(tok);
		if(i == config_def.start_col)
			start=atol(tok);
		if(i == config_def.end_col)
			end=atol(tok);
		if(i >= config_def.base_col_start) {
            sum = atof(tok);
            col_idx_real = (*col_idx)-config_def.base_col_start;
			(*vals)[col_idx_real] += sum;
			(*vals2)[col_idx_real] = sum;
            (*total_sum) += sum;
        }
		i++;
		tok = strtok(NULL,delim);
	}
    if(!first)
    {
        //assume BED format (start half open interval)
        (*ilen) = end - start;
        if(print_coord)
            fprintf(stdout,"%s\t%lu\t%lu",chrm,start,end);
    }
	if(line_copy)
		free(line_copy);
	if(!first && chrm)
		free(chrm);
	if(line)
		free(line);
	return i;
}

//parameters for the program
static struct option long_opts[] = 
{
	//can be 0 (ROW) or 1 (COLUMN)
	{"axis", required_argument, 0, 'a'},
	//can be "sum" or "mean", or "all" (for both)
	{"op", required_argument, 0, 'o'},
	//short, descriptive name/id to be used per row or for the final single row
	//(depending on axis)
	{"label", required_argument, 0, 'l'},
	{0,0,0,0}
};

config_settings setup(int argc, char*** argv)
{
	int opt_;
	int opt_idx = 0;

	config_settings config_def;
	config_def.chrm_col=0;
	config_def.start_col=1;
	config_def.end_col=2;
	config_def.base_col_start=3;
	config_def.axis=COL_AXIS;
	config_def.op = "sum";
	config_def.label = "";
	config_def.filter=501;

	opt_ = getopt_long(argc, *argv, "a:o:l:f:", long_opts, &opt_idx);
	while(opt_ != -1)
	{
		switch(opt_)
		{
		case 'a':
			config_def.axis = atoi(optarg);
			break;
		case 'o':
			config_def.op = optarg;
			break;
		case 'l':
			config_def.label = optarg;
			break;
		case 'f':
			config_def.filter = atoi(optarg);
		case '?':
			break;
		default:
			exit(-1);
		}
		opt_idx = 0;
		opt_ = getopt_long(argc, *argv, "a:o:l:", long_opts, &opt_idx);
	}
	//printf("axis: %d op: %s label: %s\n",config_def.axis,config_def.op,config_def.label);
	return config_def;
}

uint64_t filter_vals(double* vals, int64_t val_len, double filter_by)
{
    uint64_t num_filtered = 0;
    int i = 0;
    for(i=0; i < val_len; i++)
        num_filtered += vals[i] >= filter_by?1:0;
    return num_filtered;
}


//modified from https://stackoverflow.com/questions/3501338/c-read-file-line-by-line
int main(int argc, char** argv)
{
	config_settings config_def = setup(argc, &argv);	
	char* line = NULL;
	size_t length = 0;
	ssize_t bytes_read = 0;
	double* vals;
	double* vals2;
	int num_vals = 0;
	long num_rows = 0;
	int first = 1;
	bytes_read=getline(&line, &length, stdin);
	//we only print coordinates if doing row-by-row (COL_AXIS) summaries
	int print_coords_per_row = config_def.axis == COL_AXIS;
    bool mean = strcmp(config_def.op, "mean") == 0;
    bool sum = strcmp(config_def.op, "sum") == 0;
    bool all = strcmp(config_def.op, "all") == 0;
    double total_sum = 0.0;
    uint64_t num_filtered = 0;
    double total_mean = 0.0;
	while(bytes_read != -1)
	{
		//assumes no header
		num_rows++;
        total_sum = 0.0;
        uint64_t ilen = 0;
		int num_toks = process_line(first, strdup(line), "\t", &vals, &vals2, config_def, print_coords_per_row, &total_sum, &ilen);
		//if the first line, we need to know the total # of samples, so make 2 passes through the line
		if(first)
		{
			num_vals = num_toks - config_def.base_col_start;
			//one large calloc up front, this array will be resused subsequently for each line
			vals = calloc(num_vals,sizeof(double));
			vals2 = calloc(num_vals,sizeof(double));
			first = 0;
            total_sum = 0.0;
			num_toks = process_line(first, strdup(line), "\t", &vals, &vals2, config_def, print_coords_per_row, &total_sum, &ilen);
		}
		if(config_def.axis == COL_AXIS)
		{
            if(sum || all)
				fprintf(stdout,"\t%.0f",total_sum);
				//fprintf(stdout,"\t%.0f",vals[0]);
			if(mean || all) {
                total_mean = total_sum/ilen;
				fprintf(stdout,"\t%.3f",total_mean);
				//fprintf(stdout,"\t%.3f",vals[0]/num_vals);
            }
            if(all) {
                num_filtered = filter_vals(vals2, num_vals, config_def.filter);
				fprintf(stdout,"\t%lu",num_filtered);
            }
			printf("\n");
			fflush(stdout);
		}
		//reset the value for a col computation
		//no need to reset for a row computation, as we
		//keep the running stat for all rows
		if(config_def.axis == COL_AXIS)
			vals[0] = 0.0;
		bytes_read=getline(&line, &length, stdin);
	}
	if(config_def.axis == ROW_AXIS)
	{
		if(strlen(config_def.label) > 0)
			fprintf(stdout,"%s",config_def.label);
		int j;
		for(j=0; j < num_vals; j++)
		{
			if(strcmp(config_def.op, "mean") == 0)
				fprintf(stdout,"\t%.3f",vals[j]/num_rows);
			else
				fprintf(stdout,"\t%.0f",vals[j]);
		}
		printf("\n");
		fflush(stdout);
	}
	if(line)
		free(line);
	if(vals)
		free(vals);
}

