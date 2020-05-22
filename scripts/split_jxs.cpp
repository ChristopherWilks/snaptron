//#include <iostream>
//#include <sstream>
//#include <fstream>
//#include <memory>
//#include <array>
#include <string>
#include <string.h>
#include <unistd.h>
#include <cstdlib>

//quick split of stdin into N number of lines per file
//specifically made to create splits of jx tsv files
//to bed format for parallel runs of UCSC liftover

int LINE_BUF_SZ=1048576;


int main(int argc, char** argv)
{
	int o;
    int num_lines = 0;
    std::string out_prefix;
	while((o  = getopt(argc, argv, "n:p:")) != -1) {
		switch(o) 
		{
			case 'n': num_lines = atol(optarg); break;
			case 'p': out_prefix = optarg; break;
        }
    }
    if(out_prefix.length() == 0 || num_lines == 0) 
    {
        fprintf(stderr,"You must pass: 1) -n number of lines per file 2) -p for outfile prefix\n");
        exit(-1);
    }
    char delim = '\t'; 
    char* ofn = new char[1024]; 
	size_t length = -1;
    char* buf = new char[LINE_BUF_SZ];
    //plenty to hold start coordinate
    char* start = new char[50];
    uint64_t start_coord = -1;
    uint32_t i = 0;
    int fidx,j,z;
    fidx = j = z = 0;
    int second_tab_pos = -1;
    int third_tab_pos = -1;
    sprintf(ofn,"%s.%d", out_prefix.c_str(), fidx);
    ssize_t bytes_read = getline(&buf, &length, stdin);
    FILE* fout = fopen(ofn, "w");
	while(bytes_read != -1)
    {
        i++;
        if(i > num_lines)
        {
            fclose(fout);
            fidx++;
            sprintf(ofn, "%s.%d", out_prefix.c_str(), fidx);
            fout = fopen(ofn, "w");
            i = 1;
        }
        z=0;
        while(buf[z] != '\t')
            z++;
        buf[z] = '\0';
        //print out first field (chrm)
        fprintf(fout, "%s\t", buf);
        z++;
        j=0;
        while(buf[z] != '\t')
            start[j++] = buf[z++];
        start[j]='\0';
        start_coord = atol(start);
        //turn into bed file start coordinate
        start_coord--; 
        fprintf(fout, "%lu\t", start_coord);
        second_tab_pos = z;
        z++;
        while(buf[z] != '\t')
            z++;
        third_tab_pos = z;
        buf[third_tab_pos] = '\0';
        //print out end coordinate (unmodifed) + 2 additional tabs
        //== 2 empty fields to use with liftover -bedPlus=2
        fprintf(fout, "%s\t\t\t", &(buf[second_tab_pos+1]));
        //then print out rest of line
        fprintf(fout, "%s", &(buf[third_tab_pos+1]));
        
        bytes_read = getline(&buf, &length, stdin);
    }
    fclose(fout);
    fprintf(stdout,"FINISHED\n");
}
        
