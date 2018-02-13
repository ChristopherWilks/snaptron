#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const int BASE_COL_START = 3;
const int CHRM_COL=0;
const int START_COL=1;
const int END_COL=2;

int process_line(char* line, char* delim, char** chrm, long* start, long* end, double** counts, int first)
{
	char* tok = strtok(line, delim);
	int i = 0;
	while(tok != NULL)
	{
		if(first)
		{
			i++;
			tok = strtok(NULL,delim);
			continue;
		}
		if(i == CHRM_COL)
		{
			*chrm=strdup(tok);
			//check top see if we're at the group boundary
			if(strncmp(*chrm,"chr",3) != 0)
			{
				free(line);
				return -1;
			}
		}
		if(i == START_COL && *start == 0)
			//offset of +1 for BED starts
			*start=atol(tok)+1;
		if(i == END_COL)
			*end=atol(tok);
		if(i >= BASE_COL_START)
			(*counts)[i-BASE_COL_START] += atof(tok);
		i++;
		tok = strtok(NULL,delim);
	}
	if(line)
		free(line);
	return i;
}


//originally based on https://stackoverflow.com/questions/3501338/c-read-file-line-by-line
int main(int argc, char* argv)
{
	char* line = NULL;
	double* counts;
	char* chrm=NULL;
	char* prev_chrm=NULL;
	
	long start=0;
	long end=-1;
	long bp_length=0;
	int first = 1;
	int num_counts = 0;
	int k = 0;
	
	size_t length = 0;
	ssize_t bytes_read = 0;
	bytes_read=getline(&line, &length, stdin);
	while(bytes_read != -1)
	{
		if(chrm)
		{
			if(prev_chrm)
				free(prev_chrm);
			prev_chrm = chrm;
		}
		int num_toks = process_line(strdup(line), "\t", &chrm, &start, &end, &counts, first);
		if(first)
		{
			num_counts = num_toks - BASE_COL_START;
			counts = calloc(num_counts,sizeof(double));
			first = 0;
			num_toks = process_line(strdup(line), "\t", &chrm, &start, &end, &counts, first);
		}
		if(num_toks == -1)
		{	
			//overwrite newline in group label
			chrm[bytes_read-1]='\0';
			bp_length = (end-start)+1;
			printf("%s\t%lu\t%s\t%lu\t%lu",chrm,bp_length,prev_chrm,start,end);
			start = 0;
			for(k=0;k<num_counts;k++)
			{
				printf("\t%.0f",counts[k]);
				counts[k]=0.0;
			}
			printf("\n");
		}
		fflush(stdout);
		bytes_read=getline(&line, &length, stdin);
	}
	fflush(stdout);
	if(line)
		free(line);
	if(prev_chrm)
		free(prev_chrm);
	if(chrm)
		free(chrm);
	if(counts)
		free(counts);
}
