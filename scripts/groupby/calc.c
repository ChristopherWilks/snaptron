#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct config_def {
	int bp_col;
	int chrm_col;
	int start_col;
	int end_col;
	int base_col_start;
	int axis;
	char* op;
} config_settings;

int process_line(char* line, char* delim, double* value, config_settings config_def, int print_coord) //double** counts
{
	char* line_copy = strdup(line);
	char* tok = strtok(line_copy, delim);
	int i = 0;
	char* chrm;
	long start, end;
	while(tok != NULL)
	{
		if(i == config_def.chrm_col)
			chrm=strdup(tok);
		if(i == config_def.start_col)
			start=atol(tok);
		if(i == config_def.end_col)
			end=atol(tok);
		if(i >= config_def.base_col_start)
		{
			if(strcmp(config_def.op, "sum") == 0 || strcmp(config_def.op, "mean") == 0)
				*value += atof(tok);
			//(*counts)[i-config_def.base_col_start] += atof(tok);
		}
		i++;
		tok = strtok(NULL,delim);
	}
	if(strcmp(config_def.op, "mean") == 0)
		*value /= (i - config_def.base_col_start);
	if(print_coord)
	{
		fprintf(stdout,"%s\t%lu\t%lu",chrm,start,end);
	}
	if(line_copy)
		free(line_copy);
	if(line)
		free(line);
	if(chrm)
		free(chrm);
	return i;
}
//modified from https://stackoverflow.com/questions/3501338/c-read-file-line-by-line
int main(int argc, char** argv)
{
	
	config_settings config_def;
	config_def.chrm_col=0;
	config_def.start_col=1;
	config_def.end_col=2;
	config_def.base_col_start=3;
	
	config_def.axis=0;
	if(argc >= 2)
		config_def.axis = atoi(argv[1]);
	config_def.op = "sum";
	if(argc >= 3)
		config_def.op = argv[2];

	char* line = NULL;
	size_t length = 0;
	ssize_t bytes_read = 0;
	bytes_read=getline(&line, &length, stdin);
	double val = 0.0;
	double* vals;
	while(bytes_read != -1)
	{
		val = 0.0;
		int num_toks = process_line(strdup(line), "\t", &val, config_def, 1);
		if(strcmp(config_def.op, "mean") == 0)
			fprintf(stdout,"\t%.3f\n",val);
		else
			fprintf(stdout,"\t%.0f\n",val);
		fflush(stdout);
		bytes_read=getline(&line, &length, stdin);
	}
	if(line)
		free(line);
}

