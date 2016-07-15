#!/usr/bin/python

# ./simulation.py <no of tg> <read or not trlist>

import simpy
import pickle
import math
import colorama
import pdb
import sys
import random
from colorama import Fore, Back, Style
colorama.init()
txt_tg = Fore.RED  + ('tg') + Style.RESET_ALL
txt_tc = Fore.BLUE + ('tokchk') + Style.RESET_ALL

sim_duration        = 15
capacity            = 4
no_of_tg            = int(sys.argv[1])
read_rate           = True if len(sys.argv) > 2 else False
capacity_multiplier = 1	# to keep req_rate below capacity
ms                  = 1.0/1000	# millisecond converter
c2serverDelay       = 0	# in ms e.g. 10ms as 10*ms   
basedelay			= 100 # network delay w/o cables
reqcnt_tg           = [ 0 for i in range(no_of_tg) ] # instanataneous count
reqrate_tg          = [ 0 for i in range(no_of_tg) ] # to save it properly
reqrate_tg_del      = [ 0 for i in range(no_of_tg) ] # to save it properly
wait_list     		= [ [ 0 for i in range(1000)] for i in range(no_of_tg) ]
wait_list_del 		= [ [ 0 for i in range(1000)] for i in range(no_of_tg) ]


# time,rate list
# this is a sample input , will be changed in runtime
tr_list = []

server_fp	= 'server.txt'
wait_fp		= open('watitime.txt', 'w')
refired_fp	= []




class Cable(object):
    """this class represents the propagation through a cable1"""
    def __init__(self, env, delay):
        self.env = env
        self.delay = delay
        self.store = simpy.Store(env, 2)	#capacity=2

    def latency(self, value):
        yield self.env.timeout(self.delay)
        self.store.put(value)

    def put(self, value):
        self.env.process(self.latency(value))

    def get(self):
        return self.store.get()


import pprint
def newTrlist( sby10 ):
	# tr = time, rate list
	# sby10 is the duraion of the load profile in second / 10
    min_duration = 1
    min_rate = 1
    global tr_list
    tr_list = []
    for i in range( no_of_tg ):
        tempSecs = 0
        templist = []
        while tempSecs < sby10:
            currentdur =  random.randint( min_duration, int(sim_duration) )	#*0.2/10
            tempSecs += currentdur
            rate = capacity 	# rate = random.randint( min_rate, int(capacity*capacity_multiplier) )
            templist.append( (currentdur, rate ) )	#*10
        tr_list.append( templist )
    # # add bursts now
    # c1 = random.randint( 0 , len( tr_list )-1 )
    # c2 = random.randint( 0 , len( tr_list[c1] )-1 )
    # # now make a spike
    # tr_list[c1][c2] = ( tr_list[c1][c2][0] ,tr_list[c1][c2][1]+ int( capacity*2 ) )


def client(env, idx, cable1, cable2, cable3, cable4):
	# print( cable1.store.items )
	# process which randomly generates messages
	# pattertime - time instanataneous time for each TokenGen
    pktno = 0
    firepattern = tr_list[idx]
    fp_idx = 0;
    pattertime = firepattern[fp_idx][0] 
    print "intial pattertime: ", pattertime
    while True:
    	print "\nfp_idx: ", fp_idx, "patter:", pattertime
        if pattertime < env.now:
            if len( firepattern ) == fp_idx+1 :
                break
            fp_idx += 1
            pattertime += firepattern[fp_idx][0]
        randrate = firepattern[ fp_idx ][1]  #random.randint( int( firepattern[fp_idx][1]*0.30 )+1 , int(firepattern[fp_idx][1]*1.70) )
        yield env.timeout( 1.0/randrate )
        pktno += 1
        cable1.put([pktno, env.now])       # sent data to tg
        print ('pkt-%d client %.3f ==> '+txt_tg+'%d \n') % ( pktno, env.now, idx)
        # print "cable1:", cable1.store.items


def client_shadow( env, idx, cable1, cable2, cable3, cable4 ):
    while True:
        msg = yield cable2.get()           # get response from tg
        print ('pkt-%d client %.3f <== '+txt_tg+'%d %.3f \n') % ( msg[0], env.now, idx , msg[1])
        env.process(wait_and_put( env, idx, cable1, cable2, cable3, cable4, msg))


def wait_and_put( env, idx, cable1, cable2, cable3, cable4, msg ):
    yield env.timeout( msg[2] )            # wait fo the time got
    cable3.put( [ msg[0] , env.now] )      # sent data to tc
    print(('pkt-%d client %.3f ==> '+txt_tc+' %0.1f') % (msg[0], env.now, msg[1] ) )
    # refired_fp[idx].write(('pkt-%d lg%d %.3f ==> '+txt_tc + '\n') % (msg[0],idx, env.now))
    msg = yield cable4.get()               # get data from tc
    # display web page
    print(('pkt-%d client %.3f <== '+txt_tc+' %0.1f') % (msg[0], env.now, msg[1] ) )


def TokenGen(env, idx, cable1, cable2):
	# A process which consumes messages.
	# update new values in wait_list_del ( left of = )
	# and use wait_list ( right of = )

    fired_fp = open("fired"+str(idx)+'.txt', 'w')
    global reqrate_tg
    global reqrate_tg_del
    global reqcnt_tg
    while True:
        # Get event for message pipe
        msg = yield cable1.get()
        wait_list_del[idx][ int(env.now-1) ] = 0;
        print ( ('pkt-%d client %.3f ==> '+txt_tg+'%d %.3f \n') % (msg[0], msg[1], idx, env.now) )
        fired_fp.write( ('pkt-%d client %.3f ==> '+txt_tg+'%d %.3f \n') % (msg[0], msg[1], idx, env.now) )
        reqcnt_tg[idx] += 1 # we need the req count
        rotId = 0
        wait_time=0
        # find the share of capcity 
        # use share of capcity to find the waittime
        soc = getShareRatio( idx , env.now )*capacity
        print ( ('soc  %.3f %.2f \n') % ( env.now, soc ) )
        fired_fp.write( ('soc  %.3f %.2f \n') % ( env.now, soc ) )
        for i in range(1000):
            rotId =  (int(env.now) + i)%1000
            usedCap = wait_list[idx][ rotId ] 
            puc = 0;
            for j in range( len(wait_list) ):
                if j != idx:
                    puc += wait_list[j][ rotId ] 
            tuc = soc - usedCap
            if puc > 0 :
                excess_used = capacity - soc - puc
                tuc += excess_used if excess_used < 0 else 0
            if( tuc > 0 ):
                wait_list_del[idx][ rotId ]+=1;
                wait_time = i;
                break
            else:
                continue
        print ( ('pkt-%d time %.3f waittime %d \n') % (msg[0], env.now, wait_time) )
        wait_fp.write( ('pkt-%d waittime %.3f %d \n') % (msg[0], env.now, wait_time) )
        cable2.put( [ msg[0] , env.now , wait_time ] )

# helper functions
def getShareRatio(idx , now):
    global reqrate_tg
    if int( now ) == 0:
        return 1.0/no_of_tg
    if( sum( reqrate_tg ) == 0 ) :
        return 1/no_of_tg
    if reqrate_tg[idx] == 0:
        reqrate_tg[idx] = 1
    return float(reqrate_tg[idx]) / sum( reqrate_tg )
    # return float(reqcnt_tg[idx]) / sum( reqrate_tg )	# bug here


def nwDelySim( env ):
    # network delay simulator -> simulate nw dely without cables
    global wait_list
    global wait_list_del
    global reqrate_tg
    global reqrate_tg_del
    global basedelay
    global ms
    while True:
        yield env.timeout(basedelay*ms) #*no_of_tg/10)
        wait_list = unshared_copy( wait_list_del )
        reqrate_tg = unshared_copy( reqrate_tg_del )


def unshared_copy(inList):
    if isinstance(inList, list):
        return list( map(unshared_copy, inList) )
    return inList


# =====================MAIN================================

if not read_rate:
    print( "generate new tr_list..." )
    # use loadprofile.txt for readability
    with open( 'loadprofile.txt' , 'w') as lpfp:
    	newTrlist( sim_duration )	#/10
        pprint.pprint( tr_list , stream=lpfp )
    # also pickle it
    # import pdb; pdb.set_trace()	#this is just python debugger
    print( tr_list )
    with open( 'loadprofile.pickle' , 'w') as lpfp:
        pickle.dump( tr_list, lpfp )
    sys.exit()
else:
    # print( "read from pickle" )
    # unpickle
    with open( 'loadprofile.pickle' , 'rb') as lpfp:
        tr_list = pickle.load( lpfp )
        print( tr_list )

# setup and start the simulation

env = simpy.Environment()
cable1 = [ Cable(env , c2serverDelay) for i in range(no_of_tg) ] # from client to tg
cable2 = [ Cable(env , c2serverDelay) for i in range(no_of_tg) ] # from tg to client
cable3 = Cable(env   , c2serverDelay) # from client to check
cable4 = Cable(env   , c2serverDelay) # from check  to client
cable5 = Cable(env   , c2serverDelay) # from check  to server
cable6 = Cable(env   , c2serverDelay) # from server to check

# print( cable3.store.items )

for i in range( no_of_tg):
    env.process(client(env, i, cable1[i], cable2[i], cable3, cable4))
    env.process(client_shadow(env,i, cable1[i], cable2[i], cable3, cable4))
    env.process(TokenGen(env, i, cable1[i], cable2[i]))

refired_fp= [open("refired"+str(idx)+'.txt', 'w') for idx in range(no_of_tg) ] 

# env.process(TokenCheck(env, cable3, cable4, cable5, cable6))
# env.process(server(env, cable5, cable6))
# env.process(logger(env))
env.process(nwDelySim(env))

env.run(until=sim_duration)

print( "run draw graphs" )
