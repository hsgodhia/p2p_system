Network topology
---------------
There are two goals while we setup the network topology for the P2P network of pigs:

1. The network is connected, there should be atleast one path from any pig to any other pig
2. Each pig is connected to a limited number of other pigs to reflect real world P2P networks where obtaining a fully connected network is not possible

We achieve this by building a hybrid structured P2P network. First, each pig connects to the pig having an immediately lower peerid/pigid. Then it makes any additional connections randomly from the list of available peers to attain an average maximum degree 'k'. Although, since this later process is random, sometimes a node may have degree slightly more than k although it is far from the trivial case of a fully connected network. As of now the degree is set as 2. This can be changed in the line 
```python
pig.joinp2p(members, 2, debug=True)
```
in the files [file](start_pigs_localhost.py) and [file](remote_driver.py)

* A model in which all k connections were made randomly was considered but then, there were cases in which disjoint cliques were being generated, thereby leading to connectivity issues.
* To replicate the test cases present in the report keep `debug=True` since otherwise the random process may generate different edge connections

Communication
-------------
The two main RPC calls which manage communication of peers is 

broadcast - used by status, status_all, take_shelter, broadcast location cordinates or any other generic broadcast
unicast - used by was_hit only as of now
was_hit - follows the path back to the sender(the one who initiated status_all) and his status would be printed in the stdout corresponding to that peer/pig

For implementation coverage we have also implemented, async_broadcast which uses asynchronous communication

Peer server/client
------------------
-Each peer is both a (server + client) and is multi-threaded to recieve messages concurrently. We instantiate the object as a singleton so all clients act on the same single remote object
-We simulate hop delays using `time.sleep()`
-When a particular pig wants to forward the message to its neighbors it uses multithreading and starts a daemon thread proportional to the number of forwardings it needs to make and executes a small worker function to forward the message
```python
t = threading.Thread(target = self.broadcast_worker, args = (pig, dup_msg,))
t.setDaemon(True)
t.start()
```

- Before a bird is launched, each pig queries for its physical neighbors and keeps a track of them. When a pig changes location, it will broadcast that to the entire network.

Concurreny
----------
We provide an atmost-once message semantic and handle duplicate messages using message Ids for each type. Each peer locally stores the messageIds it has processed corresponding to each type in the dictionary `self._msg_hist`. This also prevents infinte flooding of the network.