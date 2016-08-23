#!/bin/bash

# to generate convergence_time vs gossip_interval graph for different branch_factors
# arg1: file with all conv_data
# arg2: input file to generate_runs

while read -r line
do
	no_tg=`echo $line | cut -d" " -f1`
	br_fact=`echo $line | cut -d" " -f2`
	file_name=${no_tg}tg_${br_fact}bf_data.tmp
	echo $line | cut -d" " --fields=3,4 >> $file_name
done < $1

while read -r line
do
	no_tg=`echo $line | cut -d":" -f1`
	br_fact_range=`echo $line | cut -d":" -f2`
	plot_string=""
	for br_fact in $br_fact_range; do
		plot_string="$plot_string, '${no_tg}tg_${br_fact}bf_data.tmp' with lp t 'br_fact ${br_fact}'"
	done
	plot_string=${plot_string:2}

	gnuplot -e "
	set terminal pngcairo;
	set output 'tg_${no_tg}.png';
	set xlabel 'gossip interval';
	set ylabel 'convergence time';
	set title 'tokengen-$i  profile and soc learned';
	plot ${plot_string};
	"
done < $2

# gnuplot -e "
# set terminal pngcairo;
# set output 'tg_5.png';
# set xlabel 'gossip interval';
# set ylabel 'convergence time';
# set title 'tokengen-$i  profile and soc learned';
# plot 'data1' with lp t 'br_fact 1',
# 	 'data2' with lp t 'br_fact 2';
# "
