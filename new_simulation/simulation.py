#!/usr/bin/python

# ./simulation.py <no of tg> <read or not tr_list> <provide tr_list here in file>

import simpy
import pickle
import math
import colorama
import pdb
import sys
import random
from colorama import Fore, Back, Style
colorama.init()
txt_tg = Fore.RED  + ('tokgen') + Style.RESET_ALL
txt_tc = Fore.BLUE + ('tokchk') + Style.RESET_ALL
txt_ser = Fore.GREEN + ('server') + Style.RESET_ALL

sim_duration        = 20
capacity            = 10
no_of_tg            = int(sys.argv[1])
read_rate           = True if len(sys.argv) > 2 else False
capacity_multiplier = 0.25	# to keep req_rate below capacity
ms                  = 1.0/1000	# millisecond converter
c2serverDelay       = 0	# in ms e.g. 10ms as 10*ms   
basedelay			= 10 # network delay w/o cables
reqcnt_server       = 0
reqrate             = 0
soc_tg              = [ 0 for i in range(no_of_tg) ]
reqcnt_tg           = [ 0 for i in range(no_of_tg) ] # instanataneous count
reqrate_tg_del      = [ 0 for i in range(no_of_tg) ] # to save it properly
reqrate_tg_local    = [ [ (0, 0) for i in range(no_of_tg) ] for i in range(no_of_tg) ]
reqrate_tg_temp     = [ [ (0, 0) for i in range(no_of_tg) ] for i in range(no_of_tg) ]
wait_timestamp      = [ [ 0 for i in range(no_of_tg) ] for i in range(no_of_tg) ]
wait_list           = [ [ [ 0 for i in range(1000)] for i in range(no_of_tg) ] for i in range(no_of_tg) ]
gossip_interval     = 0.3
branch_factor       = 4

# time,rate list
# this is a sample input , will be changed in runtime
tr_list = []

config_fp   = open('config.txt', 'w')
server_fp	= 'server.txt'
wait_fp		= open('waittime.txt', 'w')
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


def client(env, idx, cable1, cable2, cable3, cable4):
	# print( cable1.store.items )
	# process which randomly generates messages
	# pattertime - time instanataneous time for each TokenGen
    pktno = 0
    firepattern = tr_list[idx]
    fp_idx = 0;
    pattertime = firepattern[fp_idx][0] 
    # print "intial pattertime: ", pattertime
    while True:
    	# print "\nfp_idx: ", fp_idx, "patter:", pattertime
        if pattertime < env.now:
            if len( firepattern ) == fp_idx+1 :
                break
            fp_idx += 1
            pattertime += firepattern[fp_idx][0]
        randrate = firepattern[ fp_idx ][1]  #random.randint( int( firepattern[fp_idx][1]*0.30 )+1 , int(firepattern[fp_idx][1]*1.70) )
        yield env.timeout( 1.0/randrate )
        pktno += 1
        cable1.put([pktno, env.now])       # sent data to tg
        print ('c-fire: pkt-%d client %.3f ==> '+txt_tg+'%d \n') % ( pktno, env.now, idx)
        # print "cable1:", cable1.store.items


def TokenGen(env, idx, cable1, cable2):
    # A process which consumes messages.
    # update new values in wait_list_del ( left of = )
    # and use wait_list ( right of = )

    fired_fp = open("fired"+str(idx)+'.txt', 'w')
    global reqrate_tg_del
    global reqcnt_tg
    while True:
        # Get event for message pipe
        msg = yield cable1.get()
        wait_list[idx][idx][ int(env.now-1) ] = 0;
        print ( ('tg-rcv: pkt-%d client %.3f ==> '+txt_tg+'%d %.3f \n') % (msg[0], msg[1], idx, env.now) )
        fired_fp.write( ('pkt-%d client %.3f ==> '+txt_tg+'%d %.3f \n') % (msg[0], msg[1], idx, env.now) )
        reqcnt_tg[idx] += 1 # we need the req count
        rotId = 0
        wait_time=0
        # find the share of capcity 
        # use share of capcity to find the waittime
        soc = getCapacityShare( idx , env.now )
        print ( ('soc: '+txt_tg+'%d %.3f %.2f \n') % (idx, env.now, soc ) )
        fired_fp.write( ('soc  %.3f %.2f \n') % ( env.now, soc ) )
        for i in range(1000):
            rotId = (int(env.now) + i)%1000
            usedCap = wait_list[idx][idx][ rotId ] 
            puc = 0;
            for j in range( len(wait_list[idx]) ):
                if j != idx:
                    puc += wait_list[idx][j][ rotId ] 
            tuc = soc - usedCap
            # print ( ('rotId: %d tuc: %d puc: %d \n') % (rotId, tuc, puc) )
            if puc > 0 :
                excess_used = capacity - soc - puc
                tuc += excess_used if excess_used < 0 else 0
                # print ( ('tuc: %d excess_used: %d \n') % (tuc, excess_used) )
            if( tuc > 0 ):
                print ( ('tuc: '+txt_tg+'%d %.3f %.2f \n') % ( idx, env.now, tuc ) )
                fired_fp.write( ('tuc  %.3f %.2f \n') % ( env.now, tuc ) )
                wait_list[idx][idx][ rotId ]+=1;
                wait_time = i;
                break
            else:
                continue
        wait_timestamp[idx][idx] = env.now
        print ( (txt_tg+'%d pkt-%d time %.3f waittime %d \n') % (idx, msg[0], env.now, wait_time) )
        wait_fp.write( ('pkt-%d waittime %.3f %d \n') % (msg[0], env.now, wait_time) )
        cable2.put( [ msg[0] , env.now , wait_time ] )


def client_shadow( env, idx, cable1, cable2, cable3, cable4 ):
    while True:
        msg = yield cable2.get()           # get response from tg
        print ('c-frcv: pkt-%d client %.3f <== '+txt_tg+'%d %.3f \n') % ( msg[0], env.now, idx , msg[1])
        env.process(wait_and_put( env, idx, cable1, cable2, cable3, cable4, msg))


def wait_and_put( env, idx, cable1, cable2, cable3, cable4, msg ):
    yield env.timeout( msg[2] )            # wait fo the time got
    cable3.put( [ msg[0] , env.now] )      # sent data to tc
    print( ('c-refire: pkt-%d client %.3f ==> '+txt_tc+' %0.3f \n') % (msg[0], env.now, msg[1] ) )
    # refired_fp[idx].write(('pkt-%d lg%d %.3f ==> '+txt_tc + '\n') % (msg[0],idx, env.now))
    msg = yield cable4.get()               # get data from tc
    # display web page
    print( ('c-rfrcv: pkt-%d client %.3f <== '+txt_tc+' %0.3f \n') % (msg[0], env.now, msg[1] ) )


def TokenCheck( env, cable3, cable4 ,cable5, cable6):
    while True:
        msg = yield cable3.get()
        print( ('tc-rcv: pkt-%d client %.3f ==> '+txt_tc+' %.3f \n') % (msg[0], msg[1], env.now) )
        cable5.put( [msg[0] , env.now] )  # sent to server
        msg = yield cable6.get()
        print( ('tc-rcv: pkt-%d '+txt_tc+' %.3f <== '+txt_ser+' %.3f \n') % (msg[0], env.now, msg[1]) )
        # get response from server 
        cable4.put( [ msg[0], env.now] )


def server( env, cable5, cable6 ):
    global reqcnt_server
    while True:
        msg = yield cable5.get()
        print(('s-rcv: pkt-%d '+txt_tc+' %.3f ==> '+txt_ser+' %.3f \n') % (msg[0], msg[1], env.now))
        reqcnt_server = reqcnt_server + 1
        if( reqrate < capacity ):
            yield env.timeout( 1.0/capacity )       # server response time  = 1/capacity
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
        yield env.timeout( 0.001 )
        if env.now - prevt > 1:
            prevt = env.now
            print ((  '%.3f reqrate_server %s\n' )% (env.now, reqcnt_server) )
            fp.write((  '%.3f reqrate_server %s\n' )% (env.now, reqcnt_server) )
            reqrate = reqcnt_server
            reqcnt_server = 0
            for i in range(no_of_tg) :
                print ((  '%.3f reqrate_tg%d %s \n' )% (env.now,i,reqcnt_tg[i] ) )
                fp.write((  '%.3f reqrate_tg%d %s\n' )% (env.now,i,reqcnt_tg[i] ) )
                reqrate_tg_del[i] = reqcnt_tg[i]
                reqcnt_tg[i] = 0;


def nwDelySim( env ):
    # network delay simulator -> simulate nw dely without cables
    global reqrate_tg_del
    global reqrate_tg_temp
    while True:
        yield env.timeout(basedelay*ms) #*no_of_tg/10)
        # wait_list = unshared_copy( wait_list_del )
        # reqrate_tg = unshared_copy( reqrate_tg_del )
        for i in range(no_of_tg):
            reqrate_tg_temp[i][i] = (round(env.now,4), reqrate_tg_del[i])


def read_data( env, idx ):
    global reqrate_tg_temp
    global reqrate_tg_local
    prevt = env.now
    while True:
        yield env.timeout( 0.001 )
        if env.now - prevt > gossip_interval:
            # print (("time: %.3f idx: %d ->")% (env.now, idx)),
            # for i in range(no_of_tg):
            #     print reqrate_tg_local[idx][i], reqrate_tg_temp[idx][i], ",",
            prevt = env.now
            # print "\npeers ->",
            tg_list=[i for i in range(0, no_of_tg) if i!=idx]
            peer_list=random.sample(tg_list, branch_factor)
            for peer in peer_list:
                # print peer,
                # get request_rate of peer
                for i in range(no_of_tg):
                    if(reqrate_tg_temp[peer][i][0]>reqrate_tg_temp[idx][i][0]):
                        reqrate_tg_temp[idx][i]=reqrate_tg_temp[peer][i]
                # get wait_list of peer
                if (wait_timestamp[peer][peer]>wait_timestamp[idx][peer]):
                    wait_list[idx][peer] = unshared_copy( wait_list[peer][peer] )
                    wait_timestamp[idx][peer] = wait_timestamp[peer][peer]

            # print (("\ntime: %.3f idx: %d ->")% (env.now, idx)),
            # for i in range(no_of_tg):
            #     print reqrate_tg_local[idx][i], reqrate_tg_temp[idx][i], ",",
            # print "\n"


# helper functions
def getCapacityShare(idx , now):
    global soc_tg
    global reqrate_tg_local
    global reqrate_tg_temp
    if int( now ) == 0:
        print "case 0",
        soc_tg[idx] = (1.0/no_of_tg) * capacity;
        return soc_tg[idx]
    for i in range(no_of_tg):
        if (reqrate_tg_temp[idx][i][0]==0):
            print "case 1",
            return soc_tg[idx]
    if reqrate_tg_local[idx][idx][1] == 0:
        reqrate_tg_local[idx][idx] = (reqrate_tg_local[idx][idx][0], 1)
    tot_reqrate = 0
    for i in range(no_of_tg):
        reqrate_tg_local[idx][i] = reqrate_tg_temp[idx][i]
        reqrate_tg_temp[idx][i] = (0, 0)
        tot_reqrate += reqrate_tg_local[idx][i][1]
    if ( tot_reqrate == 0 ):
        print "case 2",
        soc_tg[idx] = (1.0/no_of_tg) * capacity;
        return soc_tg[idx]
    soc_tg[idx] = (float(reqrate_tg_local[idx][idx][1]) / tot_reqrate) * capacity
    print "case 3", reqrate_tg_local[idx][idx], " -> ", tot_reqrate,
    return soc_tg[idx]


def unshared_copy(inList):
    if isinstance(inList, list):
        return list( map(unshared_copy, inList) )
    return inList


# write setup configuration to file
def write_config():
    config_fp.write(('sim_duration \t\t = %d \n')% sim_duration)
    config_fp.write(('capacity \t\t = %d \n')% capacity)
    config_fp.write(('no_of_tg \t\t = %d \n')% no_of_tg)
    config_fp.write(('capacity_multiplier \t = %.3f \n')% capacity_multiplier)
    config_fp.write(('c2serverDelay \t\t = %d \n')% c2serverDelay)
    config_fp.write(('basedelay \t\t = %d \n')% basedelay)
    config_fp.write(('gossip_interval \t = %.3f \n')% gossip_interval)
    config_fp.write(('branch_factor \t\t = %d \n')% branch_factor)


# function to generate new time rate list
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
            currentdur =  random.randint( min_duration, int(sim_duration*0.4/10) )
            tempSecs += currentdur
            rate = random.randint( min_rate, int(capacity*capacity_multiplier) )
            templist.append( (currentdur*10, rate ) )
        tr_list.append( templist )
    # add bursts now
    c1 = random.randint( 0 , len( tr_list )-1 )
    c2 = random.randint( 0 , len( tr_list[c1] )-1 )
    # now make a spike
    tr_list[c1][c2] = ( tr_list[c1][c2][0] ,tr_list[c1][c2][1]+ int( capacity*2 ) )



# =====================MAIN================================

if not read_rate:
    print( "generate new tr_list..." )
    # use loadprofile.txt for readability
    with open( 'loadprofile.txt' , 'w') as lpfp:
    	newTrlist( sim_duration/10 )
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

# to provide tr_list explicitly
if (len(sys.argv) > 3):
    tr_list = [[(10, 1), (40, 20), (200, 1)],
               [(200, 1)],
               [(200, 1)],
               [(200, 1)],
               [(200, 1)]]
    with open( 'loadprofile.txt' , 'w') as lpfp:
        pprint.pprint( tr_list , stream=lpfp )
    with open( 'loadprofile.pickle' , 'w') as lpfp:
        pickle.dump( tr_list, lpfp )

print( tr_list )
write_config()


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
    env.process(read_data(env, i))

refired_fp= [open("refired"+str(idx)+'.txt', 'w') for idx in range(no_of_tg) ] 

env.process(TokenCheck(env, cable3, cable4, cable5, cable6))
env.process(server(env, cable5, cable6))
env.process(logger(env))
env.process(nwDelySim(env))

env.run(until=sim_duration)

print( "run draw graphs script" )
