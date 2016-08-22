#!/bin/bash

# fist parameter is the no of tg, second is weather to read list or
# not
rm -rf *.txt *.tmp *.png
./simulation.py "$@"
