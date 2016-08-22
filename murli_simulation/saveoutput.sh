#!/bin/bash 

FOLDER=`date +'%F_%H%M%S'`_$1
mkdir ${FOLDER}
mv *.txt *.tmp *.png $FOLDER
cp loadprofile.pickle $FOLDER
