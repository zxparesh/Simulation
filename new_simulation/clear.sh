#!/bin/bash

# Usage:
# no arg -> delte all generated files
# any arg -> delete only drawgraph.sh generated files

if [ $# -eq 0 ];
then
	rm *.txt *.tmp *.png
else
	rm *.tmp *.png
fi
