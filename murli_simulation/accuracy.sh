#!/bin/bash

# this assumes the presence of 1-60tg folders

# run convergence test and 

# z10tg/
# z1tg/
# z20tg/
# z2tg/
# z30tg/
# z3tg/
# z40tg/
# z4tg/
# z50tg/
# z5tg/
# z60tg/
# z6tg/
# z7tg/
# z8tg/
# z9tg/

capacity=700
minTGval=12
# for i in `seq 1 1 9` `seq 10 10 60`; do #for nooftg/convtiem
#     awk '{if($2>'${i}'*'$minTGval'){print }}' y${i}tg/server.tmp | awk \
#         '{sum+=$2}END{print '$i',2-(sum/NR/'$capacity')}'
# done

i=20  # no of tokegens
# for timedelaytest.sh
for ms in `seq 100 50 400`; do #for nooftg/convtiem
    awk '{if($2>'${i}'*'$minTGval'){print }}' x_${i}tg_${ms}ms/expected_server.tmp | awk \
        '{sum+=$2}END{print '$ms',2-(sum/NR/'$capacity')}'
done
