for i in `seq 1 1 9` `seq 10 10 60`; do #for nooftg/convtiem
# for i in 5; do      # for nwdelay/convtime
    echo $i
    fol=$i; ./simulation.sh $fol read ; ./drawgraph.sh; ./saveoutput.sh ${fol}tg
    # BE carefull of ???? mark globbing .. wil point to same folder
    # fol=$i; awk '{ if( int($1)>=90 && int($2)>=(1400/(('$fol'-1)*10+1400)*700*.96) ) {print ; exit } }' 2016-06-09_??????${fol}tg/0soc.tmp
    # echo "removing files"
    # rm -r 2016-06-09_??????${fol}tg
done
