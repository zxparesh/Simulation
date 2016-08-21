#!/usr/bin/python

import sys

# arg1: ground_truth file
# arg2: soc experimental file
# arg3: output filename

fin1 = sys.argv[1]
fin2 = sys.argv[2]
# fout = sys.argv[3]

fin1_pt = open(fin1, 'r')
fin2_pt = open(fin2, 'r')
# fout_pt = open(fout, 'w')

soc = int(-1)
con_time = 0
con_count = 0
	
for line in fin1_pt:
	line = line.split();
	ttime = float(line[0])
	tsoc = int(float(line[1]))
	if (tsoc != soc):
		for nline in fin2_pt:
			nline = nline.split();
			nsoc = int(float(nline[1]))
			ntime = float(nline[0])
			if (ntime>=ttime and nsoc == tsoc):
				con_count += 1
				con_time += ntime-ttime
				break;
		soc = tsoc

print float(con_time/con_count)
