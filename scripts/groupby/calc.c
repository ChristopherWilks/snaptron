#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>

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
} config_settings;

//tokenize each line to get the coordinates and the list of sample counts
//if doing a axis=COLUMN computation do it per row here
int process_line(int first, char* line, char* delim, double** vals, config_settings config_def, int print_coord)
{
	char* line_copy = strdup(line);
	char* tok = strtok(line_copy, delim);
	int i = 0;
	char* chrm;
	long start, end;
	int static_idx = config_def.base_col_start;
	int* col_idx = &static_idx;
	if(config_def.axis == ROW_AXIS)
		col_idx = &i;
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
		if(i >= config_def.base_col_start)
		{
			if(strcmp(config_def.op, "sum") == 0 || strcmp(config_def.op, "mean") == 0)
				(*vals)[(*col_idx)-config_def.base_col_start] += atof(tok);
		}
		i++;
		tok = strtok(NULL,delim);
	}
	if(!first && print_coord)
		fprintf(stdout,"%s\t%lu\t%lu",chrm,start,end);
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
	//can be "sum" or "mean"
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

	opt_ = getopt_long(argc, *argv, "a:o:l:", long_opts, &opt_idx);
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


//modified from https://stackoverflow.com/questions/3501338/c-read-file-line-by-line
int main(int argc, char** argv)
{
	config_settings config_def = setup(argc, &argv);	
	char* line = NULL;
	size_t length = 0;
	ssize_t bytes_read = 0;
	double* vals;
	int num_vals = 0;
	long num_rows = 0;
	int first = 1;
	bytes_read=getline(&line, &length, stdin);
	//we only print coordinates if doing row-by-row (COL_AXIS) summaries
	int print_coords_per_row = config_def.axis == COL_AXIS;
	while(bytes_read != -1)
	{
		//assumes no header
		num_rows++;
		int num_toks = process_line(first, strdup(line), "\t", &vals, config_def, print_coords_per_row);
		//if the first line, we need to know the total # of samples, so make 2 passes through the line
		if(first)
		{
			num_vals = num_toks - config_def.base_col_start;
			//one large calloc up front, this array will be resused subsequently for each line
			vals = calloc(num_vals,sizeof(double));
			first = 0;
			num_toks = process_line(first, strdup(line), "\t", &vals, config_def, print_coords_per_row);
		}
		if(config_def.axis == COL_AXIS)
		{
			if(strcmp(config_def.op, "mean") == 0)
				fprintf(stdout,"\t%.3f",vals[0]/num_vals);
			else
				fprintf(stdout,"\t%.0f",vals[0]);
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

