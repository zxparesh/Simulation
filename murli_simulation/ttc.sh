for i in `seq 1 1 9` `seq 10 10 60`; do #for nooftg/convtiem
    fol=$i; awk '{ if( int($1)>=90 && int($2)>=(1400/(('$fol'-1)*10+1400)*700*.96) ) 
    {print '$i',$0 ; exit } }' x${fol}tg/0soc.tmp
done
