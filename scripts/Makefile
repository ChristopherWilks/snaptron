all: filter split_jxs mmformat filter2mmformat

filter: filter_sjs_by_samples.cpp
	g++ -O3 -std=c++11 filter_sjs_by_samples.cpp -o filter

debug: filter_sjs_by_samples.cpp
	g++ -g -std=c++11 filter_sjs_by_samples.cpp -o filter-debug

split_jxs: split_jxs.cpp
	g++ -O3 -std=c++11 split_jxs.cpp -o split_jxs

mmformat: mmformat.cpp
	g++ -O3 -std=c++11 mmformat.cpp -o mmformat

mmformat-debug: mmformat.cpp
	g++ -g -std=c++11 mmformat.cpp -o mmformat-debug

filter2mmformat: filter2mmformat.cpp
	g++ -O3 -std=c++11 filter2mmformat.cpp -o filter2mmformat

clean: 
	rm -f filter filter-debug split_jxs mmformat filter2mmformat mmformat-debug
