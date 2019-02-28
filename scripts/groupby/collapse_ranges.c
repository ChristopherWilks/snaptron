#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const int BASE_COL_START = 3;
const int CHRM_COL=0;
const int START_COL=1;
const int END_COL=2;

int process_line(char* line, char** prev, char** chrm1, long* start1, long* end1, char*** coords)
{
    //replace the following with just a loop over the start of the line
    //just the coordinate fields (break off at the 2nd tab)
    //then compare the pointer at this line vs. the previous line ptr
	int i = 0;
    int num_tabs = 0;
    int j = 0;
    while(num_tabs < 3)
    {
        while(line[i] != '\t')
            (*coords)[num_tabs][j++] = line[i++];
        //move past the tab
        i++;
        (*coords)[num_tabs][j] = '\0';
        j = 0;
        num_tabs++;
    }
    //check 1) we're not first 2) chrms match and 3) count strings match to previous line
    if((*start1) != -1 && strcmp(*chrm1, (*coords)[0]) == 0 && strcmp(&(line[i]), *prev) == 0)
    {
            //extending previous range
            *end1 = atol((*coords)[2]);
            if(line)
                free(line);
            return i;
    }
    if(*start1 != -1)
    {
        //print out previous range
        fprintf(stdout,"%s\t%lu\t%lu\t%s",*chrm1,*start1,*end1,*prev);
		fflush(stdout);
        /*free(*chrm1);
        free(*prev);*/
    }
    //start a new range
    int stl = strlen((*coords)[0]);
    //should only happen once
    if(!(*chrm1))
        *chrm1 = calloc(sizeof(char), stl+10);
    //*chrm1 = strdup((*coords)[0]);
    memmove(*chrm1, (*coords)[0], stl);
    (*chrm1)[stl]='\0';
    *start1 = atol((*coords)[1]);
    *end1 = atol((*coords)[2]);

    stl = strlen(&(line[i]));
    if(!(*prev))
        *prev = calloc(sizeof(char), (10*stl) + 1);
    memmove(*prev, &(line[i]), stl);
    (*prev)[stl]='\0';
    //(*prev) = strdup(&(line[i]));
    if(line)
        free(line);
	return -1;
}


//originally based on https://stackoverflow.com/questions/3501338/c-read-file-line-by-line
int main(int argc, char* argv)
{
	char* line = NULL;
	char* chrm=NULL;
	long start=-1;
	long end=-1;
    char *prev = NULL;
	
    char** coords = calloc(sizeof(char*),3);
    coords[0] = calloc(sizeof(char),13);
    coords[1] = calloc(sizeof(char),13);
    coords[2] = calloc(sizeof(char),13);
	
    size_t length = 0;
	ssize_t bytes_read = 0;
    int num_toks = 0;

    FILE* finf = stdin;
    /*FILE* inf = fopen("test1","r");
    finf = inf;*/
	bytes_read=getline(&line, &length, finf);
	while(bytes_read != -1)
	{
		num_toks = process_line(strdup(line), &prev, &chrm, &start, &end, &coords);
		bytes_read=getline(&line, &length, finf);
	}
    if(start != -1)
    {
        //print out previous range
        fprintf(stdout,"%s\t%lu\t%lu\t%s",chrm,start,end,prev);
		fflush(stdout);
    }
	if(line)
		free(line);
	if(chrm)
		free(chrm);
    if(prev)
        free(prev);
    free(coords[0]);
    free(coords[1]);
    free(coords[2]);
    free(coords);
}
