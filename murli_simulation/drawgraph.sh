#!/bin/bash


# draw for each token gen

NOTG=$((`ls fired*.txt | wc -l` - 1))

for i in `seq 0 $NOTG` ; do 
    cat fired$i.txt | awk '/pkt/ {print int($3)}'| sort -n | uniq -c | awk '{print $1}' > $i.tmp
    cat fired$i.txt | awk '/soc/ {print  $2, $3}'                                       > ${i}soc.tmp
    gnuplot -e "
    set terminal pngcairo;
    set output 'sent$i.png';
    set title 'tokengen-$i  profile and soc learned';
    plot '$i.tmp' with lp t 'incoming load',
         '${i}soc.tmp' with lp t 'share of capacity';
    "
done

cat fired*.txt | awk '/pkt/ {print int($3)}'| sort -n | uniq -c | awk '{print $1}' > cum.tmp

gnuplot -e "
set terminal pngcairo;
set output 'sent_cum.png';
set title 'cumulative profile - "`ls fire*|wc -l`" tokengen used';
plot 'cum.tmp' with lp ;
"


cat server.txt | awk '/server/ {print int($1),$3}' > server.tmp

gnuplot -e "
set terminal pngcairo;
set title 'server: actual at the server';
set output 'recieved.png';
plot 'server.tmp' with lp;
"


cat watitime.txt| awk '{print $3,$4 }' > waittime.tmp


gnuplot -e "
set terminal pngcairo;
set output 'waittime.png';
set title 'waittime assined to each incoming';
plot 'waittime.tmp' ;
"


cat waittime.tmp | awk '{print int($1)+$2}' | uniq -c | awk '{asd[$2]+=$1}END{for(a in asd){print a, asd[a]}}' | sort -n > expected_server.tmp

gnuplot -e "
set terminal pngcairo;
set output 'expected_recieved.png';
set title 'server: expected load profile at server';
plot 'expected_server.tmp' w l;
"


# draw a cumulative inbound grapsh


gnuplot -e "
set terminal pngcairo;
set output 'all_inbound.png';
set title 'all inbound';
plot for [i=0:$NOTG] ''.i.'.tmp' with lp title 'tg'.i,
                'cum.tmp' with lp t 'cumulative'
"
