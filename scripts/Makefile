all: filter

filter: filter_sjs_by_samples.cpp
	g++ -O3 -std=c++11 filter_sjs_by_samples.cpp -o filter

debug: filter_sjs_by_samples.cpp
	g++ -g -std=c++11 filter_sjs_by_samples.cpp -o filter-debug

clean: 
	rm filter filter-debug
