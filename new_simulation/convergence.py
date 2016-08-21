#!/usr/bin/python

# You can call this function with:
# arg1: ground_truth file (format: time soc)
# arg2: soc experimental file (format: time soc)

def findConvergenceTime(file1, file2):

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

	return float(con_time/con_count)
