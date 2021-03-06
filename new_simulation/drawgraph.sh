#!/bin/bash


# read parameters from config.txt

DURATION=`awk '/sim_duration/ {print int($3)}' config.txt`
CAPACITY=`awk '/capacity / {print int($3)}' config.txt`
NOTG=$((`awk '/no_of_tg/ {print int($3)}' config.txt`-1))
BRN_FACT=`awk '/branch_factor/ {print $3}' config.txt`
GOS_INT=`awk '/gossip_interval/ {print $3}' config.txt`

###### draw for each token_gen ######

# generate soc ground truth values

python soc_ground_truth.py loadprofile.pickle $CAPACITY $DURATION

# NOTG=$((`ls fired*.txt | wc -l` - 1))

# imcoming load, soc exp, soc gt_value vs time

for i in `seq 0 $NOTG` ; do 
    cat fired$i.txt | awk '/pkt/ {print int($3)}'| sort -n | uniq -c | awk '{print $1}' > $i.tmp
    cat fired$i.txt | awk '/soc/ {print  $2, $3}'                                       > ${i}soc.tmp
    gnuplot -e "
    set terminal pngcairo;
    set output 'sent$i.png';
    set title 'tokengen-$i  profile and soc learned';
    plot '$i.tmp' with lp t 'incoming load',
         '${i}soc.tmp' with lp t 'share of capacity',
         '${i}soc_gt.tmp' with lp t 'ground truth share of capacity';
    "
done


# cumulative load (sum of all tokengens)

cat fired*.txt | awk '/pkt/ {print int($3)}'| sort -n | uniq -c | awk '{print $1}' > cum.tmp

gnuplot -e "
set terminal pngcairo;
set output 'sent_cum.png';
set title 'cumulative profile - "`ls fire*|wc -l`" tokengen used';
plot 'cum.tmp' with lp ;
"


# number of requests served by server

cat server.txt | awk '/server/ {print int($1),$3}' > server.tmp

gnuplot -e "
set terminal pngcairo;
set title 'server: actual at the server';
set output 'recieved.png';
plot 'server.tmp' with lp;
"


# waittime assigned to each incoming request

cat waittime.txt| awk '{print $3,$4 }' > waittime.tmp

gnuplot -e "
set terminal pngcairo;
set output 'waittime.png';
set title 'waittime assined to each incoming';
plot 'waittime.tmp' ;
"


# expected number of requests at server

cat waittime.tmp | awk '{print int($1)+$2}' | uniq -c | awk '{asd[$2]+=$1}END{for(a in asd){print a, asd[a]}}' | sort -n > expected_server.tmp

gnuplot -e "
set terminal pngcairo;
set output 'expected_recieved.png';
set title 'server: expected load profile at server';
plot 'expected_server.tmp' w l;
"


# draw a cumulative inbound graphs

gnuplot -e "
set terminal pngcairo;
set output 'all_incoming.png';
set title 'all incoming';
plot for [i=0:$NOTG] ''.i.'.tmp' with lp title 'tg'.i,
                'cum.tmp' with lp t 'cumulative'
"


# avg convergence time of all token_gen

con_time=0
for i in `seq 0 $NOTG` ; do
    c_time=`python convergence.py ${i}soc_gt.tmp ${i}soc.tmp`
    con_time=`echo $con_time + $c_time | bc`
done

# avg=$(echo "$con_time/$NOTG" | bc -l)

no_tg=$(($NOTG + 1))

avg=$(echo "scale=4; $con_time/$no_tg" | bc -l)

echo $no_tg $BRN_FACT $GOS_INT $avg > converg_time.tmp
