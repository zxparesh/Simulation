#!/usr/bin/python
from __future__ import division
import pickle
import sys


# arg1 = pickle file
# arg2 = capacity of server
# arg3 = simulation duration

file = sys.argv[1]
CAP = int(sys.argv[2])
duration = int(sys.argv[3])

with open( file , 'rb') as lpfp:
    tr_list = pickle.load( lpfp )
L=[]
for i in tr_list:
	temp=[]
	for j in i:
		temp.extend([j[1]]*j[0])
	L.append(temp)
	temp=[]


Max=max([len(i) for i in L])


new_L=[]

for i in L:
	if Max-len(i)>0:
		i.extend([0]*(Max-len(i)))
		new_L.append(i)
	else: 
		new_L.append(i)


final=zip(*new_L)

results=[]
for i in final:
	temp=[]
	Sum=sum(i)
	for j in i:
		temp.append(round(j/Sum*CAP))
	results.append(temp)

results=zip(*results)

j=0
for i in results:
	f=open(str(j)+"soc_gt.tmp","w")
	j+=1
	l=0
	for k in i:
		f.write(str(l)+" "+str(k)+"\n")
		l+=1
		if(l>duration):
			break
f.close()