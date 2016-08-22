tg=20
for i in `seq 100 50 400`; do
    echo $i ms
    sed -i 's/basede.*=.*/basedelay='$i'/' simulation.py
   ./simulation.sh $tg read; ./drawgraph.sh; ./saveoutput.sh _${tg}tg_${i}ms
done
