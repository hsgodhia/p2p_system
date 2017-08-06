import os, sys
import Pyro4, time, Pyro4.util
from point import Point

DEBUG_MODE = True
DEGREE = 2
Pyro4.config.SERIALIZER = 'pickle'
sys.excepthook = Pyro4.util.excepthook
uri = "PYRO:peer@"
members = {}

def setup_p2p():
    with open("hostinfo.txt", 'r') as fp:
        content = fp.readlines()

    for line in content:
        dt = line.split(" ")
        members[int(dt[0])] = dt[1]

    #initialize network topology, each peer connects to randomly choosen 3 others
    kys = list(members.keys())
    kys.sort(reverse=True)
    for m in kys:
        pig = Pyro4.Proxy(uri + members[m])
        pig.joinp2p(members, DEGREE, debug=DEBUG_MODE)

    for m in members:
        pig = Pyro4.Proxy(uri + members[m])
        pig.getnet_topo()

setup_p2p()