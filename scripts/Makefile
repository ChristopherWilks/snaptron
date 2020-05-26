all: filter split_jxs mmformat

filter: filter_sjs_by_samples.cpp
	g++ -O3 -std=c++11 filter_sjs_by_samples.cpp -o filter

debug: filter_sjs_by_samples.cpp
	g++ -g -std=c++11 filter_sjs_by_samples.cpp -o filter-debug

split_jxs: split_jxs.cpp
	g++ -O3 -std=c++11 split_jxs.cpp -o split_jxs

mmformat: filter2mmformat.cpp
	g++ -O3 -std=c++11 filter2mmformat.cpp -o mmformat

clean: 
	rm filter filter-debug split_jxs mmformat
