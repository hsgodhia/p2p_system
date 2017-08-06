How to run
----------
This program depends on and uses Python 3.6 and Pyro 4.55, and when issuing python commands use "python3" if both python 2.x and 3.x is installed on the system.

#### Following are the steps to play the game:

 1. Start the pig servers
 2. Setup the p2p network 
 3. Run the game driver

1. To start pig servers, depending upon the option of running locally or remote follow the steps below

 -To run locally
  - To run all pigs on a single machine, we have written a utility bash [script](src/startpigslocal.sh) which will start the pigs by reading the `hostinfo.txt` [file](src/hostinfo.txt) passed as a command line argument
  - Issue the command `./startpigslocal.sh hostinfo.txt` to start the pigs
  - When all peers are run on the localhost/same machine, each peer redirects `stdout` to a file `output_<peerId>.txt`
  - [startpigslocal](src/startpigslocal.sh) has `python3` in its command, since edlab has two python versions, if python 3.x is the only installation, change it to `python`
 
 -To run each pig on separate remote machines
  - Each pig or peer is started using the command
	`python3 peer.py <peerId> <ip_addr:port>` 
  - When run remotely each peer should be started in a separate terminal since `stdout` is not re-directed automatically and prints on terminal
  - the ip_addr can be looked up using the command /sbin/ifconfig on edlab machines. Use this ipaddr to run the above command, and choose a non conflicting port number such as 44000. You would also have to correspondingly update the [hostinfo](src/hostinfo.txt) file with these ip address and port numbers

  * Note: The `peerId` and `ip_addr:port` have to be consistent with the `hostinfo.txt` [file](src/hostinfo.txt) contents
  * In case, the file throws a connection refused error, please edit the `hostinfo.txt` and assign different port numbers to the host/pigs. 

2. To setup the p2p network
 - For both remote and local runs choose one of the pig/terminal and issue the following command
`python3 setup_p2pnet.py`
 - The program `setup_p2pnet.py` reads the contents of the file `hostinfo.txt` and *will setup the P2P network* between the machines mentioned in the hostinfo file
 - In the above program the below line forms the network 
 ```python
pig.joinp2p(members, DEGREE, debug=DEBUG_MODE)
 ```
 - by default `DEBUG_MODE` is `True` which creates a network topology matching the one mentioned in our report, change it to `False` to enable random connections
 - also you may increase the average degree of each node, by changing `DEGREE` whose default is set to `2`

3. Now we run the game
 - For both remote and local runs choose a terminal and issue the following command
`python3 game_driver.py < gameinput.txt`
 - This program starts the main game loop which launches birds and prints scores for each round. It depends on the `game_input.txt` file to read information for each round

* To edit the files `hostinfo.txt` and `gameinput.txt` read the [input format](doc/InputDescription.md)
* Our game assumption and rules are mentioned [here](doc/GameRules.md)
* Our design is described [here](doc/Design.md)
* Some improvements are decribed [here](doc/caveats.md)
* Once the game is over, and you want to kill the pigs there is no automatic way to kill them, please run `ps -a | grep python` to find the PIDs and issue `kill -9`
* `chmod a+x startpigslocal.sh` to make it executable permission

Files
-----

1. peer.py - The main implementation of a peer in the P2P network 

2. message.py - Each message sent over the P2P network is an instance of message.py which supports 8 message types
```python
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
```

3. peerinterface.py - Describes the main interface methods which we implement in peer.py

4. point.py - a wrapper for cordinates (x,y)

5. hostinfo.txt - input file for host information see [input descriptions](doc/InputDescription.md) for more details

6. gameinput.txt - game input with all test cases included see [input descriptions](doc/InputDescription.md) for more details. note we have not written unit test cases but performed functional testing by including more than 5 test caes here.

7. gameinput_remote.txt - the same as `gameinput.txt` only with fewer test cases and fewer pigs/peers which we used to test remotely on edlab
