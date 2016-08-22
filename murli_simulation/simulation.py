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

SIM_DURATION        =  120 #200
NO_OF_TG            = int(sys.argv[1])
capacity            = 700
reqcnt_server       = 0
reqcnt_tg           = [ 0 for i in range(NO_OF_TG) ]  # instanataneous coutn
reqrate_tg          = [ 0 for i in range(NO_OF_TG) ] # to save it properly
reqrate_tg_del      = [ 0 for i in range(NO_OF_TG) ] # to save it properly
reqrate             = 0
READ_RATE           = True if len(sys.argv) > 2 else False
CAPACITY_MULTIPLIER = 0.25
basedelay=100
ms                  = 1.0/1000
c2serverDelay       = 0 #10*ms   


# time , rate
# this is a sample input , will be changed in runtime
tr_list = []

fired_FP='fired'
server_fp='server.txt'
refired='refired'
wfp = open('watitime.txt', 'w')

refiredFP = []

# 1000 by 1000 wait list array
wait_list     = [ [ 0 for i in range(1000)] for i in range(NO_OF_TG) ]
wait_list_del = [ [ 0 for i in range(1000)] for i in range(NO_OF_TG) ]

class Cable(object):
    """This class represents the propagation through a cable1."""
    def __init__(self, env, delay):
        self.env = env
        self.delay = delay
        self.store = simpy.Store(env, 2)

    def latency(self, value):
        yield self.env.timeout(self.delay)
        self.store.put(value)

    def put(self, value):
        self.env.process(self.latency(value))

    def get(self):
        return self.store.get()


def wait_and_put( env, idx, cable1, cable2, cable3, cable4, msg ):
    yield env.timeout( msg[2] )            # wait for the time got
    cable3.put( [ msg[0] , env.now] )      # sent data to tc
    refiredFP[idx].write(('pkt-%d lg%d %.3f ==> '+txt_tc + '\n') % (msg[0],idx, env.now))
    msg = yield cable4.get()               # get data from tc
    # display web page
    # print(('pkt-%d client %.3f <== '+txt_tc+' %0.1f') % (msg[0], env.now, msg[1] ) )

# print( cable1.store.items )
def client(env, idx, cable1, cable2, cable3, cable4):
    """A process which randomly generates messages.
    pattertime - time instanataneous time for each TokenGen
    """
    pktno = 0
    firepattern = tr_list[idx]
    fp_idx = 0;
    pattertime = firepattern[fp_idx][0] 
    while True:
        if pattertime < env.now:
            if len( firepattern ) == fp_idx+1 :
                break
            fp_idx += 1
            pattertime += firepattern[fp_idx][0]
        randrate = firepattern[ fp_idx ][1]  #random.randint( int( firepattern[fp_idx][1]*0.30 )+1 , int(firepattern[fp_idx][1]*1.70) )
        yield env.timeout( 1.0/randrate )
        pktno += 1
        cable1.put([pktno, env.now])       # sent data to tg

def client_shadow( env, idx, cable1, cable2, cable3, cable4 ):
    while True:
        msg = yield cable2.get()           # get response from tg
        # print(('pkt-%d client %.3f <== '+txt_tg+'%d %.3f \n') % ( msg[0], env.now, idx , msg[1]) )
        env.process(wait_and_put( env, idx , cable1, cable2, cable3, cable4,msg ))


def TokenGen(env, idx, cable1, cable2):
    """A process which consumes messages.
        update new values in wait_list_del ( left of = )
        and use wait_list ( right of = )
    """
    fp = open(fired_FP+str(idx)+'.txt', 'w')
    global reqrate_tg
    global reqrate_tg_del
    global reqcnt_tg
    while True:
        # Get event for message pipe
        msg = yield cable1.get()
        wait_list_del[idx][ int(env.now-1) ] = 0;
        fp.write( ('pkt-%d client %.3f ==> '+txt_tg+'%d %.3f \n') % (msg[0] , msg[1], idx, env.now) )
        reqcnt_tg[idx] += 1 # we need the req count
        rotId = 0
        wait_time=0
        # find the share of capcity 
        # TODO 
        #use share of capcity to find the waittime
        soc = getShareRatio( idx , env.now )*capacity
        fp.write( ('soc  %.3f %.2f \n') % ( env.now, soc ) )
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
        wfp.write( ('pkt-%d waittime %.3f %d \n') % (msg[0], env.now, wait_time) )
        cable2.put( [ msg[0] , env.now , wait_time ] )

def TokenCheck( env, cable3, cable4 ,cable5, cable6):
    while True:
        msg = yield cable3.get()
        # print(('pkt-%d client %.3f ==> '+txt_tc+' %.3f ') % (msg[0], msg[1], env.now))
        cable5.put( [msg[0] , env.now] )  # sent to server
        msg = yield cable6.get()
        # print(('\t\t pkt-%d '+txt_tc+' %.3f <== server %.3f') % (msg[0], env.now, msg[1]))
        # get response from server 
        cable4.put( [ msg[0], env.now] )

def server( env, cable5, cable6 ):
    # print(('\t\t pkt-%d '+txt_tc+'%.3f ==> server %.3f ') % (msg[0], msg[1], env.now))
    global reqcnt_server
    while True:
        msg = yield cable5.get()
        reqcnt_server = reqcnt_server + 1
        if( reqrate < capacity ):
            yield env.timeout( 1.0/900 )       # server response time  = 1/capacity
        else:
            yield env.timeout( 1 )
        cable6.put( [ msg[0] , env.now ] )

def logger( env ): 
    global reqcnt_server
    global reqcnt_tg
    global reqrate_tg_del
    fp = open( server_fp , 'w' )
    prevt = env.now
    while True:
        yield env.timeout( 0.01 )
        if env.now - prevt > 1:
            prevt = env.now
            fp.write((  '%.3f req_rate_server %s\n' )% (env.now, reqcnt_server) )
            reqrate = reqcnt_server
            reqcnt_server = 0
            for i in range(NO_OF_TG) :
                fp.write((  '%.3f req_rate_tg%d %s\n' )% (env.now,i,reqcnt_tg[i] ) )
                reqrate_tg_del[i] = reqcnt_tg[i]
                reqcnt_tg[i] = 0;

def nwDelySim( env ):
    # network Delay simulator -> simulate nw dely without cables
    global wait_list
    global wait_list_del
    global reqrate_tg
    global reqrate_tg_del
    global basedelay
    global ms
    while True:
        yield env.timeout(basedelay*ms) #*NO_OF_TG/10)
        wait_list = unshared_copy( wait_list_del )
        reqrate_tg = unshared_copy( reqrate_tg_del )

def unshared_copy(inList):
    if isinstance(inList, list):
        return list( map(unshared_copy, inList) )
    return inList

# helper functions
def getShareRatio(idx , now):
    global reqrate_tg
    if int( now ) == 0:
        return 1.0/NO_OF_TG
    if( sum( reqrate_tg ) == 0 ) :
        return 1/NO_OF_TG
    if reqrate_tg[idx] == 0:
        reqrate_tg[idx] = 1
    return float(reqrate_tg[idx]) / sum( reqrate_tg )
    # return float(reqcnt_tg[idx]) / sum( reqrate_tg ) #bug

import pprint
def newTrlist( sby10 ):
    '''
        Tr = time, rate list
        sby10 is the duraion of the load profile in second / 10
    '''
    MIN_DURATIN = 2
    global tr_list
    tr_list = []
    for i in range( NO_OF_TG ):
        tempSecs = 0
        templist = []
        while tempSecs < sby10:
            currentdur =  random.randint( 1 , int(SIM_DURATION*0.2/10) )
            tempSecs += currentdur
            rate = random.randint( 1 , int(capacity*CAPACITY_MULTIPLIER) )
            templist.append( (currentdur*10, rate ) )
        tr_list.append( templist )
    # add bursts now
    c1 = random.randint( 0 , len( tr_list )-1 )
    c2 = random.randint( 0 , len( tr_list[c1] )-1 )
    # now make a spike
    tr_list[c1][c2] = ( 
                    tr_list[c1][c2][0] ,
                    tr_list[c1][c2][1]+ int( capacity*2 ) 
                    )

# =====================MAIN================================

if not READ_RATE:
    print( "make new list" )
    # use loadprofile.txt for readabiliyt
    with open( 'loadprofile.txt' , 'w') as lpfp:
        newTrlist( SIM_DURATION/10 )
        pprint.pprint( tr_list , stream=lpfp )
    # also pickle it
    import pdb; pdb.set_trace()
    with open( 'loadprofile.pickle' , 'w') as lpfp:
        pickle.dump( tr_list, lpfp )
    sys.exit()
else:
    # print( "read from pickle" )
    # unpickle
    with open( 'loadprofile.pickle' , 'rb') as lpfp:
        tr_list = pickle.load( lpfp )
        # print( tr_list )

# Setup and start the simulation

env = simpy.Environment()
cable1 = [ Cable(env , c2serverDelay) for i in range(NO_OF_TG) ] # from client to tg
cable2 = [ Cable(env , c2serverDelay) for i in range(NO_OF_TG) ] # from tg to client
cable3 = Cable(env   , c2serverDelay) # from client to check
cable4 = Cable(env   , c2serverDelay) # from check  to client
cable5 = Cable(env   , c2serverDelay) # from check  to server
cable6 = Cable(env   , c2serverDelay) # from server to check

for i in range( NO_OF_TG):
    env.process(client(env, i, cable1[i], cable2[i], cable3, cable4))
    env.process(client_shadow(env,i, cable1[i], cable2[i], cable3, cable4))
    env.process(TokenGen(env, i, cable1[i], cable2[i]))

refiredFP= [open(refired+str(idx)+'.txt', 'w') for idx in range(NO_OF_TG) ] 

env.process(TokenCheck(env, cable3, cable4, cable5, cable6))
env.process(server(env, cable5, cable6))
env.process(logger(env))
env.process(nwDelySim(env))
env.run(until=SIM_DURATION)
print( "run draw graphs" )

# run an experiment and see if the resutl changes .. kadichupidi
# input rate at each token gen
# communicate b/w tokengens and draw graphs , make report
# TODO and experiment wth small diff values
