all: groupby_tabix groupby_general

groupby_tabix: groupby_tabix.c
	gcc -O3 groupby_tabix.c -o groupby_tabix
groupby_general: groupby_general.c
	gcc -O3 groupby_general.c -o groupby_general
calc: calc.c
	gcc -O3 calc.c -o calc

clean: 
	rm groupby_tabix groupby_general
