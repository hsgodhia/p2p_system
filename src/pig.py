class Pig(object):
    def __init__(self, id, addr, handle):
        self.id = id
        self.addr = addr
        self.handle = handle
    
    def __str__(self):
        return "{0} is at {1} and address is {2}".format(self.id, self.handle.get_location(), self.addr)