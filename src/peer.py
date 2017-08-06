import Pyro4, random, sys, copy, math, Pyro4.util, socket, time
from point import Point
from message import Message, MsgType
from peerinterface import PeerInterface
import threading

Pyro4.config.SERIALIZERS_ACCEPTED = set(['pickle'])
Pyro4.config.SERIALIZER = 'pickle'
sys_random = random.SystemRandom()
_lock = threading.Lock()
@Pyro4.expose
@Pyro4.behavior(instance_mode="single")

class Peer(PeerInterface):
    def __init__(self, data):
        self._daemon_obj = data['daemon']
        #unique identifier for each pig/peer
        self._peerId = data['id']
        #an incrementing sequence for each pig(used as message ids to identify each communication uniquely)
        self._incr_index = self._peerId*100000
        #message id storage/history to avoid duplicates
        self._msg_hist = {MsgType.BIRD:[], MsgType.STATUS:[], MsgType.LOCATION:[], MsgType.SHELTER:[], MsgType.REACHABLE:[], MsgType.RESET:[], MsgType.ROLLOVER:[], MsgType.PILLAR:[]}
        #pig location
        self._location = data.get('location', None)
        #all time units in peer.py are in seconds
        #bird time to impact, reset at each bird launch
        self._bird_time = 0
        #peer hop delay
        self._hopcount_delay = data.get('hop_delay', 0)
        #network neighbors
        self._neighbors = {}

    # --begin--
    # implementation of interface methods
    def take_shelter(self, peerId):
        #calculate potential rollover point
        moves = self.getNextMoves(self._location)
        valid_moves = []
        for m in moves:
            if m not in self._pillars:
                valid_moves.append(m)
        potential_rollover_at = valid_moves[0]

        self._incr_index += 1
        # generate next id and send message of type shelter
        msg = Message(MsgType.SHELTER, self._incr_index, [], 0, False, (self._peerId, peerId, potential_rollover_at, self._bird_time))
        # message sent via network broadcast/flooding
        self.broadcast(msg)

    def bird_approaching(self, point, hopcount):
        self._incr_index += 1        
        data = (point, self._bird_time)
        # generate next id and send bird approaching message with payload as point of impact and time to impact
        msg = Message(MsgType.BIRD, self._incr_index, [], hopcount, True, data)
        self.broadcast(msg)
        # message sent via network broadcast/flooding

    def status(self, peerId):
        self._incr_index += 1
        msg_ig = self._incr_index
        # generate next id and send status message with payload of request peerid
        msg = Message(MsgType.STATUS, msg_ig, [], 0, False, peerId)
        self.broadcast(msg)
        # message sent via network broadcast/flooding
    
    def status_all(self):
        # -1 is a special indicator for a broadcast, message is sent throughout the network and every pig should respond
        self._scores.clear()
        self.status(-1)
        # wait for all scores to reach, will not work if peer count changes and dynamically peers exit/enter (use async calls and timeout in that case)
        while (1):
            if len(self._scores) == self._peergrpsize:
                break
        # if some pig has a status of None, 
        # indicates it didn't recieve a bird approaching message (due to hopcount being 0 for instance) and subsequently did not change his location
        
        print(self._scores, flush=True)
        return self._scores
        # return score to the game driver to track
            
    def was_hit(self, peerId, hitstatus):
        print('got response of peer {0}, his status {1} '.format(peerId, hitstatus), flush=True)
        self._scores[peerId] = hitstatus

    # extra method to handle pillar fallings
    def pillar_falling(self, point):
        self._incr_index += 1        
        data = (point, self._bird_time)
        # generate next id and send pillar falling message with payload as point of impact and time to impact
        msg = Message(MsgType.PILLAR, self._incr_index, [], 0, False, data)
        self.broadcast(msg)
        # message sent via network broadcast/flooding

    # --begin-- core communication methods
    # this method is used to return messages back to sender on originally traversed path without flooding
    def unicast(self, msg):
        if len(msg.hops) == 0:
            self.was_hit(msg.data[0], msg.data[1])
        else:
            parentId = msg.hops[-1]
            del msg.hops[-1]
            uri = 'PYRO:peer@' + self._neighbors[parentId]
            parent_pig = Pyro4.Proxy(uri)
            #extract parent from message hops and send message back
            parent_pig.unicast(msg)

    # this method broadcasts messages to entire network using flooding
    def broadcast(self, msg):
        if msg.id in self._msg_hist[msg.msg_type]:  return None
        self._msg_hist[msg.msg_type].append(msg.id)
        # we use an atmost-once message semantic
        # record each message recieved of each type to avoid duplicate processing
        if msg.msg_type == MsgType.SHELTER:
            if msg.data[1] == self._peerId:
                print ("Take shelter! {0} is going to be attacked".format(msg.data[0]), flush=True)

                potential_rollover_pt = msg.data[2]
                if self._euclidean(potential_rollover_pt) > 0.0:
                    return None
                    #this pig is safe other neightbors may be in danger
                msg_delay = len(msg.hops)*self._hopcount_delay
                
                mv = self.getEmptySpace()
                if msg.data[3] < 0 or msg_delay > msg.data[3]:
                    print("Too late to move! Already dead.", flush=True)
                    return None

                if mv is not None:
                    print("Moved! to {0}".format(mv), flush=True)
                    self._location = mv
                return None

        elif msg.msg_type == MsgType.RESET:
            self.resetpig(0)
        
        elif msg.msg_type == MsgType.STATUS:
            fwd_msg = False            
            #if status has destination -1, broadcast indicator, forward message after receiving it
            if msg.data == -1:
                fwd_msg = True
            
            if self._peerId == msg.data or msg.data == -1:
                dup_msg = Message(msg.msg_type, msg.id, list(msg.hops), msg.hopcount, msg.ishopcounted, msg.data)
                dup_msg.data = (self._peerId, self._hitstatus)
                self.unicast(dup_msg)

                if fwd_msg == False:
                    return None                
        
        elif msg.msg_type == MsgType.BIRD or msg.msg_type == MsgType.PILLAR:
            self._evade_action(msg)
            # on receiving a bird approaching message or pillar falling message take an evasive action

        elif msg.msg_type == MsgType.LOCATION:
            #check if this peerid is a neighbor, one of 4 nearest cells
            if self._isNeighbor(msg.data[1]) and self._peerId != msg.data[0]:
                self._phy_neighbors[msg.data[0]] = msg.data[1]
            
        #check for hopcount
        if msg.ishopcounted == True and msg.hopcount < 1:
            return None
        # no forwarding; stop broadcast if hopcount is counted and exhausted .. < 1

        msg.hopcount -= 1
        msg.hops.append(self._peerId)
        time.sleep(self._hopcount_delay)
        #simulate a hop dealy using sleep
        for id in self._neighbors:
            uri = "PYRO:peer@" + self._neighbors[id]
            pig = Pyro4.Proxy(uri)    
            dup_msg = Message(msg.msg_type, msg.id, list(msg.hops), msg.hopcount, msg.ishopcounted, msg.data)            
            # forward the messages in parallel to all immediate neighbors
            t = threading.Thread(target = self.broadcast_worker, args = (pig, dup_msg,))
            t.setDaemon(True)
            t.start()
            # using threads and set daemon as true,since we don't expect any return values
        
    def broadcast_worker(self, pig, msg):
        pig.broadcast(msg)
    
    def reset_all(self):
        self._incr_index += 1
        msg_id = self._incr_index
        msg = Message(MsgType.RESET, msg_id, [], 0, False, None)
        self.broadcast(msg)

    # -- begin -- network connection utility methods
    # check if self peer is reachable to all other peers/pigs
    def is_reachable(self):
        self._incr_index += 1
        msg = Message(MsgType.REACHABLE, self._incr_index, [], 0, False, None)
        res = set(self.async_broadcast(msg))
        if len(res) == self._peergrpsize:
            return True
        else:
            return False

    def async_broadcast(self, msg):
        if msg.id in self._msg_hist[msg.msg_type]:
            return []
        self._msg_hist[msg.msg_type].append(msg.id)
        if msg.msg_type == MsgType.REACHABLE:
            rch = []
            rch.append(self._peerId)
            future_results = {}
        
            for id in self._neighbors:
                rch.append(id)
                uri = "PYRO:peer@" + self._neighbors[id]
                pig = Pyro4.async(Pyro4.Proxy(uri))
                t = threading.Thread(target=self.async_broadcast_worker, args=(future_results, id, pig, copy.copy(msg), ))
                t.start()

            future_status = all([future_results[res].ready for res in future_results])
            while future_status == False:
                future_status = all([future_results[res].ready for res in future_results])
            for res in future_results:
                rch.extend(future_results[res].value)
            return rch

    def async_broadcast_worker(self, future_results, id, pig, msg):
        future_results[id] = pig.async_broadcast(msg)

    #core network topology management methods    
    def is_connected(self, degree):
        return len(self._neighbors) == degree

    def connect(self, peerId, peerhost):
        print('{0} got a connect request from {1}'.format(self._peerId, peerId), flush=True)
        self._neighbors[peerId] = peerhost

    def exitp2p(self):
        self._neighbors.clear()
            
    # takes a dict of peerids and hostinfo
    def joinp2p(self, members, degree, debug = False):
        # store the total number of peers in this p2p, dynamic exit and entries not supported
        self._peergrpsize = len(members)

        kys = list(members.keys())
        kys.sort()
        ind = kys.index(self._peerId)

        # first connect to the immediate lowest peerId (structured segment of the p2p network to ensure connectedness)
        if ind > 0:
            ngh = kys[ind - 1]
            if ngh not in self._neighbors:
                self._neighbors[ngh] = members[ngh]
                uri = 'PYRO:peer@' + members[ngh]
                neighbor_peer = Pyro4.Proxy(uri)
                neighbor_peer.connect(self._peerId, members[self._peerId])
     
        rem_degree = degree - len(self._neighbors)
        if rem_degree <= 0:
            return None
        nums = []
        for i in members:
            if i == self._peerId:
                self._address = members[i]
                continue
            elif i in self._neighbors:
                continue
            uri = 'PYRO:peer@' + members[i]
            other_pig = Pyro4.Proxy(uri)
            #if other_pig.is_connected(degree):
            #    continue
            nums.append(i)
        
        if len(nums) >= rem_degree:
            #self._peerId would connect to peers present in nums
            nums = sys_random.sample(nums, rem_degree)
            
            if debug == True:
                if self._peerId == 0:
                    nums.clear()
                    nums.append(3)
                elif self._peerId == 8:
                    nums.clear()
                    nums.append(5)

            for i in nums:
                self._neighbors[i] = members[i]
                uri = 'PYRO:peer@' + members[i]
                neighbor_peer = Pyro4.Proxy(uri)
                neighbor_peer.connect(self._peerId, members[self._peerId])
    
    def broadcast_cordinates(self):
        self._incr_index += 1
        msg = Message(MsgType.LOCATION, self._incr_index, [], 0, False, (self._peerId, self._location))
        self.broadcast(msg)

    # --begin-- game methods    
    def _evade_action(self, msg):
        msg_delay = len(msg.hops)*self._hopcount_delay
        print("pigID:{0} is at {1} and attack is at {2} in time {3}. message delay {4} and route:{5}".format(self._peerId, self._location, msg.data[0], msg.data[1], msg_delay, msg.hops), flush=True)
        dist = self._euclidean(msg.data[0])

        if dist > 0:
            return None
        #if direct impact calculate if pig is dead
        elif dist <= 0:    
            self._bird_time = msg.data[1] - msg_delay
            # inform physical neighbors to take shelter as there is a chance for a rollover
            for id in self._phy_neighbors:
                t = threading.Thread(target = self.take_shelter, args = (id,))
                t.setDaemon(True)
                t.start()

            #pig is hit=True if msg arrives later than bird time to impact
            self._hitstatus = msg.data[1] < msg_delay
            if self._hitstatus is False:
                empty_space = self.getEmptySpace()
                if empty_space is not None:
                    with _lock:
                        self._location = empty_space                    
                    print("pigID:{0} escaped to {1}".format(self._peerId, self._location),flush=True)
                                  
    def funeral(self, msg):
        #check if the pig was successful to evade and move to another location
        if self._euclidean(msg.data) == 0.0:
            self._hitstatus = True
        return self._hitstatus

    # --begin-- utility methods
    # l2 norm between self.location and location param
    def _euclidean(self, location):
        with _lock:
            dist = math.sqrt(math.pow((self._location.x - location.x), 2) + math.pow((self._location.y - location.y), 2))
        return dist
    
    # physical cordinate neighbors  
    # consider pigs which are 1 distance away to be physical neighbors
    def _isNeighbor(self, location):
        return self._euclidean(location) <= 1.0
        
    # stateful information which is reset after each bird launch/round
    #utility to reset scores, physcial cordinate neighbors and hitstatus 
    def resetpig(self, num):
        self._hitstatus = False        
        self._phy_neighbors = {}
        self._scores = {}
        print("\n-- begin round {0} --".format(num), flush=True)
    
    def getNextMoves(self, _location):
        moves = []
        # limit to only allow 4 directions of movement 
        actions = [(1,0), (0,1), (-1,0), (0,-1)]
        for a in actions:
            n_l = copy.copy(_location)
            n_l.x += a[0]
            n_l.y += a[1]
            # boundary checks
            if n_l.x >= self._grid_size or n_l.y >= self._grid_size or n_l.x < 0 or n_l.y < 0:
                continue
            moves.append(n_l)
        return moves

    def getEmptySpace(self):
        moves = self.getNextMoves(self._location)
        nghbrs = list(self._phy_neighbors.values())
        # any move not amongst the list of pillars or list of physical neighbors
        for m in moves:
            if m not in self._pillars and m not in nghbrs:
                return m
        return None
    
    # --begin-- getters and setters, physical neighbors are (unit distance away)
    def printPhyNeighbor(self):
        print("PeerId: {0} is at {1} and physical neighbor to:".format(self._peerId, self._location), flush=True)
        for n in self._phy_neighbors:
            print("PeerId: {0} at {1}".format(n, self._phy_neighbors[n]), flush=True)

    def getnet_topo(self):
        # print network topology, network neightbors
        print("PeerId: {0} is a network neighbor to: {1}".format(self._peerId, self._neighbors), flush=True)
    
    def set_gridsize(self, n):
        self._grid_size = n

    def set_bird_time(self, bird_time):
        self._bird_time = bird_time

    def set_pillars(self, pillars):
        self._pillars = []
        # each pig only keeps record of pillars in its immediate neighborhood
        for p in pillars:
            if self._euclidean(p) <= 1.0:
                self._pillars.append(p)

    def get_pillars(self):
        return self._pillars

    def set_location(self, location):
        with _lock:
            self._location = location
    
    def get_location(self):
        with _lock:
            return self._location
    
    def set_hopcount_delay(self, delay):
        self._hopcount_delay = delay
        
    def get_hopcount_delay(self):
        return self._hopcount_delay 

    def set_daemon_obj(self, ref):
        self._daemon_obj = ref

    def stoppig(self):
        self._daemon_obj.shutdown()
        self._daemon_obj.close()
        sys.exit()

if __name__ == '__main__':
    peerId = int(sys.argv[1])
    hostinfo = sys.argv[2]
    hostname = hostinfo.split(":")[0]
    hostport = int(hostinfo.split(":")[1])
    Pyro4.config.HOST = hostname
    daemon_obj = Pyro4.Daemon(hostname, hostport)
    print("peerId: {0} running with below uri".format(peerId), flush=True)
    #start peer client/server request loop
    pig = Peer({'id':peerId, 'daemon':daemon_obj})

    Pyro4.Daemon.serveSimple({pig: "peer"}, ns = False, verbose=True, daemon=daemon_obj, host=hostname, port=hostport)