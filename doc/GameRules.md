Assumptions
-----------
This game consists of a series of rounds. 
Each round, 
* will set the pigs to new cordinates (user input)
* the physical neighbors are re-discovered by a broadcast
* no state of the previous rounds is carried forward (such as, toppled pillars are restored)
* the pillars or stone columns have fixed locations which are the same in each round
* the network topology/network neighbors do not change
* each pig knows the locations of all the pillars (since they are static)

Interactions
-------------
* Each pig is allowed to move in only 4 directions, up, down, left and right
* A pig can escape from an attack and move only when an empty space is available, which is not occupied by another pig or pillar
* A pig cannot tople a pillar, it can topple or kill a neighboring other pig
* A brid lanuch can happen and strike a pillar and cause it to topple
* Whenever a pig is attack and dies as a result, it rolls over neighboring pigs killing them too, they cannot kill anyone further, hence any strike can kill atmost 2 pigs
* When a pig roll's over it choose one of the available positions in order of right, top, left, down as the cordinate to rollover to 
* When a pig broadcasts a take_shelter message to its neighbors they recieve a (MsgType.SHELTER) message, they read the payload which contains the position the striked pig may rollover to and incase that position corresponds to the pigs location it moves to any other empty space
* An empty space is discovered using the P2P network via the physical neighbors and pillars list
* For each bird launch the pig nearest to the bird will send bird_approaching message to the network, it will also later be queried for status_all
