#!/usr/bin/python

import pickle
import sys

file = sys.argv[1]

with open( file , 'rb') as lpfp:
    tr_list = pickle.load( lpfp )
    print( tr_list )
