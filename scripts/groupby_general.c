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

	int group_col;
	int subgroup_col;
	char* subgroup_delim;
} column_settings;

char* get_subgroup(char* group, column_settings col_def)
{
	char* g = strdup(group);
	char* ttok = strtok(g, col_def.subgroup_delim);
	int i = 0;
	while(ttok != NULL)
	{
		if(col_def.subgroup_col == i)
		{
			return ttok;
		}
		ttok = strtok(NULL, col_def.subgroup_delim);
		i++;
	}
	if(g)
		free(g);
	return NULL;
}

int check_group_boundary(char** group, char** prev_group, column_settings col_def)
{
	if(col_def.subgroup_col != -1)
	{
		char* subgroup = get_subgroup(*group, col_def);
		if(*group)
			free(*group);
		*group = subgroup;
	}
	if(!*prev_group)
	{
		*prev_group = *group;
		return 0;
	}
	//no subgroup, so just check group
	if(strcmp(*group, *prev_group)!=0)
		return -1;
	return 0;
}

void check_chromosome(char** chrm, char** prev_chrm)
{
	if(*chrm && *prev_chrm != *chrm)
	{
		if(*prev_chrm)
			free(*prev_chrm);
		*prev_chrm = *chrm;
	}
}


int process_line(char* line, char* delim, long* bp_length, char** chrm, char** prev_chrm, long* start, long* end, double** counts, int first, char** group, char** prev_group, int skip_group_check, column_settings col_def)
{
	char* group_line = strdup(line);
	char* tok = strtok(group_line, delim);
	int i = 0;
	while(tok != NULL)
	{
		if(first)
		{
			i++;
			tok = strtok(NULL,delim);
			continue;
		}

		//check top see if we're at the group boundary
		if(i == col_def.group_col && !skip_group_check)
		{
			*group = strdup(tok);
			if(check_group_boundary(group, prev_group, col_def)==-1)
			{
				if(group_line)
					free(group_line);
				if(line)
					free(line);
				return -1;
			}
			//if no change to the group, reset
			if(*group && *prev_group && *group != *prev_group)
			{
				free(*group);
				*group = *prev_group;
			}
			skip_group_check = 1;
			//restart the tokenization process on the original line
			tok = strtok(line, delim);
			i = 0;
		}
		if(i == col_def.bp_col)
			*bp_length+=atol(tok);
		if(i == col_def.chrm_col)
		{
			check_chromosome(chrm, prev_chrm);
			*chrm=strdup(tok);
		}
		if(i == col_def.start_col && *start == 0)
			*start=atol(tok);
		if(i == col_def.end_col)
			*end=atol(tok);
		//assume this always comes after the group/subgroup col.
		if(i >= col_def.base_col_start)
			(*counts)[i-col_def.base_col_start] += atof(tok);
		i++;
		tok = strtok(NULL,delim);
	}
	if(group_line)
		free(group_line);
	if(line)
		free(line);
	return i;
}


//modified from https://stackoverflow.com/questions/3501338/c-read-file-line-by-line
int main(int argc, char** argv)
{
	column_settings col_def;
	col_def.bp_col=1;
	col_def.chrm_col=2;
	col_def.start_col=3;
	col_def.end_col=4;

	col_def.base_col_start=5;
	col_def.group_col=0;
	col_def.subgroup_col=0;
	col_def.subgroup_delim=":";

	if(argc >= 2)
		col_def.subgroup_col = atoi(argv[1]);		
	if(argc >= 3)
		col_def.subgroup_delim = argv[2];		

	char* line = NULL;
	double* counts;
	char* chrm=NULL;
	char* prev_chrm=NULL;
	char* group=NULL;
	char* prev_group=NULL;
	
	long start=0;
	long end=-1;
	long prev_start = start;
	long prev_end = end;
	long bp_length=0;
	long prev_bp_length = bp_length;
	int first = 1;
	int num_counts = 0;
	int k = 0;
	
	size_t length = 0;
	ssize_t bytes_read = 0;
	bytes_read=getline(&line, &length, stdin);
	while(bytes_read != -1)
	{
		int skip_group_check = 0;
		int num_toks = process_line(strdup(line), "\t", &bp_length, &chrm, &prev_chrm, &start, &end, &counts, first, &group, &prev_group, skip_group_check, col_def);
		if(first)
		{
			num_counts = num_toks - col_def.base_col_start;
			//one large calloc up front
			counts = calloc(num_counts,sizeof(double));
			first = 0;
			num_toks = process_line(strdup(line), "\t", &bp_length, &chrm, &prev_chrm, &start, &end, &counts, first, &group, &prev_group, skip_group_check, col_def);
		}
		check_chromosome(&chrm, &prev_chrm);
		prev_start = start;
		prev_end = end;
		prev_bp_length = bp_length;
		if(num_toks == -1)
		{	
			//bp_length = (end-start)+1;
			printf("%s\t%lu\t%s\t%lu\t%lu",prev_group,prev_bp_length,prev_chrm,prev_start,prev_end);
			for(k=0;k<num_counts;k++)
			{
				printf("\t%.0f",counts[k]);
				counts[k]=0.0;
			}
			printf("\n");
			skip_group_check = 1;
			//process the rest of the line for the current group
			if(prev_group)
				free(prev_group);
			prev_group = group;
			start = 0;
			bp_length = 0;
			process_line(strdup(line), "\t", &bp_length, &chrm, &prev_chrm, &start, &end, &counts, first, &group, &prev_group, skip_group_check, col_def);
			prev_start = start;
			prev_end = end;
			prev_bp_length = bp_length;
			check_chromosome(&chrm, &prev_chrm);
		}
		fflush(stdout);
		bytes_read=getline(&line, &length, stdin);
	}
	if(prev_group)
	{	
		//bp_length = (end-start)+1;
		printf("%s\t%lu\t%s\t%lu\t%lu",prev_group,prev_bp_length,prev_chrm,prev_start,prev_end);
		for(k=0;k<num_counts;k++)
		{
			printf("\t%.0f",counts[k]);
			counts[k]=0.0;
		}
		printf("\n");
	}
	fflush(stdout);
	if(line)
		free(line);
	if(prev_chrm)
		free(prev_chrm);
	if(counts)
		free(counts);
	if(prev_group)
		free(prev_group);
}
