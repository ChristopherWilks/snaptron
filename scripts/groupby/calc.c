#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct col_def {
	int bp_col;
	int chrm_col;
	int start_col;
	int end_col;
	int base_col_start;
} column_settings;

int process_line(char* line, char* delim, double* value, column_settings col_def, int print_coord) //double** counts
{
	char* line_copy = strdup(line);
	char* tok = strtok(line_copy, delim);
	int i = 0;
	char* chrm;
	long start, end;
	while(tok != NULL)
	{
		if(i == col_def.chrm_col)
			chrm=strdup(tok);
		if(i == col_def.start_col)
			start=atol(tok);
		if(i == col_def.end_col)
			end=atol(tok);
		if(i >= col_def.base_col_start)
			*value += atof(tok);
			//(*counts)[i-col_def.base_col_start] += atof(tok);
		i++;
		tok = strtok(NULL,delim);
	}
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
	/*char* op;
	if(argc >= 2)
		op = argv[1];*/
	
	column_settings col_def;
	col_def.chrm_col=0;
	col_def.start_col=1;
	col_def.end_col=2;
	col_def.base_col_start=3;

	char* line = NULL;
	size_t length = 0;
	ssize_t bytes_read = 0;
	bytes_read=getline(&line, &length, stdin);
	double val = 0.0;
	while(bytes_read != -1)
	{
		val = 0.0;
		int num_toks = process_line(strdup(line), "\t", &val, col_def, 1);
		fprintf(stdout,"\t%.0f\n",val);
		fflush(stdout);
		bytes_read=getline(&line, &length, stdin);
	}
	if(line)
		free(line);
}

