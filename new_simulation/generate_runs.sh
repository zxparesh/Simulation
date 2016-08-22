#!/bin/bash

# generate and run test cases:


# for conv_time vs no_of_tg, with diff br_fact

# file format: no_tg:br_fact values e.g 50:5 10 20 25 30 40

gos_int_range="0.2 0.3 0.4 0.5 0.6 0.7"

while read -r line
do
	no_tg=`echo $line | cut -d":" -f1`
	# generate tr_list for given no of token_gen
	python simulation.py $no_tg 1 1
	echo -e "\ntr_list generated: tg:" $no_tg

	br_fact_range=`echo $line | cut -d":" -f2`
	for br_fact in $br_fact_range; do
		echo "br_fact:" $br_fact
		for gos_int in $gos_int_range; do
			echo "   gos_int:" $gos_int

			# run simulation
			python simulation.py $no_tg $br_fact $gos_int a &>> output.txt
			echo "simulation run success" &>> output.txt

			# drar graphs
			bash drawgraph.sh &>> output.txt
			echo "drawgraph success" &>> output.txt

			# save convergence time value to file
			cat converg_time.tmp >> conv_time

			# move generated files to folder
			fol_name=${no_tg}tg_${br_fact}bf_${gos_int}gi
			bash saveoutput.sh $fol_name

		done
	done
done < $1
