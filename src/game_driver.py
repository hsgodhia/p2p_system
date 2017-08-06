import Pyro4, time, Pyro4.util, sys, math, threading, random, copy
from point import Point
from message import Message, MsgType
from pig import Pig

Pyro4.config.SERIALIZER = 'pickle'
sys.excepthook = Pyro4.util.excepthook
sys_random = random.SystemRandom()

def get_pig_at(pigs, pt):    
    for i in pigs:
        pig = pigs[i]
        pig_pt = pig.handle.get_location()
        if _euclidean(pig_pt, pt) == 0.0:
            return pig

def bird_launch(n_pig, to_pt, hopcount):
    n_pig.handle.bird_approaching(to_pt, hopcount)

def pillar_fall(n_pig, to_pt, hopcount,sq_n):
    print(" to {0}".format(to_pt), flush=True)        
    n_pig.handle.pillar_falling(to_pt)

def getNextMoves(_location, _grid_size):
    moves = []
    # only allows 4 directions of movement 
    actions = [(1,0), (0,1), (-1,0), (0,-1)]
    for a in actions:
        n_l = copy.copy(_location)
        n_l.x += a[0]
        n_l.y += a[1]
        # boundary checks
        if n_l.x >= _grid_size or n_l.y >= _grid_size or n_l.x < 0 or n_l.y < 0:
            continue
        moves.append(n_l)
    return moves

def nearestpig(pigs, pt):
    min_dist = 100000
    min_pig = None
    for i in pigs:
        dist = _euclidean(pigs[i].handle.get_location(), pt)
        if dist < min_dist:
            min_dist = dist
            min_pig = pigs[i]
    return min_pig

def _euclidean(_location, location):
    dist = math.sqrt(math.pow((_location.x - location.x), 2) + math.pow((_location.y - location.y), 2))
    return dist

def isPillar(pt, pillars):
    for pl in pillars:
        if _euclidean(pt, pl) <= 0:
            return True
    return False

def driver_worker(pig_handle, pt, pillars, n, test_num):    
    #before game reset pig
    pig_handle.resetpig(test_num)
    #set new location
    pig_handle.set_location(pt)
    #broadcast cordinates
    pig_handle.broadcast_cordinates()
    #pass pillar positions which are fixed for the game board
    pig_handle.set_pillars(pillars)
    pig_handle.set_gridsize(n)


pigs = {}
uri = "PYRO:peer@"
with open("hostinfo.txt", 'r') as fp:
    content = fp.readlines()

for line in content:
    dt = line.split(" ")
    pig_h = Pyro4.Proxy(uri + dt[1])
    pig_id = int(dt[0])
    hopcount_delay = int(dt[2].rstrip())/1000
    pig_h.set_hopcount_delay(hopcount_delay)
    pig = Pig(pig_id, dt[1], pig_h)
    pigs[pig_id] = pig

sq_n = input("Enter playground/grid length(L): ")
sq_n = int(sq_n)
print(sq_n)

plr = int(input("number of pillars: "))
print(plr)
pillars = []
while plr > 0:
    dt = input()
    pillars.append(Point(tupl_str=dt))
    plr -= 1

assert len(set(pillars)) == len(pillars), "don't repeat pillars, each one in a unique location!"    
print("game rouds begin: ")
test_num = 0
while(1):
    inp = input("Enter 'y' to quit game, 'n' to continue: ")
    if inp == 'y':
        break
    test_num += 1
    print(inp)
    i = len(pigs)
    threads = []
    while i > 0:
        line = input()
        dt = line.split(" ")
        pig_id = int(dt[0])
        pt = Point(tupl_str = dt[1])
        pig_h = pigs[pig_id].handle
        t = threading.Thread(target=driver_worker, args=(pig_h,pt, pillars, sq_n, test_num, ))
        t.start()
        threads.append(t)
        i -= 1

    for t in threads:
        t.join()

    time.sleep(5)
    for i in pigs:
        pig = pigs[i]
        pig.handle.printPhyNeighbor()
    
    line = input("bird luanch info: ")
    print(line)
    desc = input("round description: ")
    print(desc)
    print("this is round {0}".format(test_num), flush=True)
    dt = line.split(" ")
    from_p = dt[0]
    from_pt = Point(tupl_str = from_p)
    to_p = dt[1]
    to_pt = Point(tupl_str = to_p)
    n_pig = nearestpig(pigs, from_pt)
    bird_time_to_impact = int(dt[2])/1000
    hopcount = int(dt[3])
    n_pig.handle.set_bird_time(bird_time_to_impact)

    if isPillar(to_pt, pillars):        
        print("You hit a pillar! It's falling from {0}".format(to_pt), flush=True, end='')
        moves = getNextMoves(to_pt, sq_n)
        to_pt = sys_random.choice(moves)
        target_pig = get_pig_at(pigs, to_pt)
        t = threading.Thread(target=pillar_fall, args=(n_pig, to_pt, hopcount,sq_n, ))
        t.setDaemon(True)
        t.start()
    else:
        target_pig = get_pig_at(pigs, to_pt)
        t = threading.Thread(target=bird_launch, args=(n_pig, to_pt, hopcount,))
        t.setDaemon(True)
        t.start()
        
    #wait till bird lands then call pig die routine
    time.sleep(bird_time_to_impact)
    time.sleep(0.1) #delta seconds for things to settle down before querying location   
    msg = Message(MsgType.DEFAULT, 0, [], 0, False, to_pt)
    chng_target_pig = get_pig_at(pigs, to_pt)
    if chng_target_pig is None or chng_target_pig.id != target_pig.id:
        hitstatus = False
    else:
        hitstatus = chng_target_pig.handle.funeral(msg)
    
    if hitstatus:
        print("You hit pigID:{0}!".format(chng_target_pig.id), flush=True)
        pig = get_pig_at(pigs, to_pt)
        
        #make pig rollover
        moves = getNextMoves(to_pt, sq_n)
        valid_moves = []
        for m in moves:
            if m not in pillars:
                valid_moves.append(m)
    
        # randomly choose a direction to rollover to
        if len(valid_moves) >= 1:
            mv = valid_moves[0]
            print("It's rolling over to {0}".format(mv), flush=True)
            pig_at_rolled_pt = get_pig_at(pigs, mv)
            if pig_at_rolled_pt is not None:
                msg = Message(MsgType.DEFAULT, 0, [], 0, False, mv)
                pig_at_rolled_pt.handle.funeral(msg)

    time.sleep(5)
    scores = n_pig.handle.status_all()
        
    print("hitstatus:{0}".format(scores), flush=True)
    hits = 0
    for k in scores:
        if scores[k]:
            hits += 1
    print("{0} hits! this round.\n".format(hits), flush=True)