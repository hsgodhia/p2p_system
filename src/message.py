from enum import Enum
class MsgType(Enum):
    DEFAULT = 0
    BIRD = 1
    STATUS = 2
    LOCATION = 3
    SHELTER = 4
    REACHABLE = 5
    RESET = 6
    PILLAR = 7
    ROLLOVER = 8
    
class Message(object):
    def __init__(self, msg_type, id, hops, hopcount, ishopcounted, data):
        self.id = id
        self.data = data
        self.msg_type = msg_type
        self.hops = hops
        self.hopcount = hopcount
        self.ishopcounted = ishopcounted
    
    def __repr__(self):
        return "carrying message:{0} of type:{1} with payload:{2} and traveled:{3}".format(self.id, self.msg_type, self.data, self.hops)
            
    def __str__(self):
        return "carrying message:{0} of type:{1} with payload:{2} and traveled:{3}".format(self.id, self.msg_type, self.data, self.hops)
