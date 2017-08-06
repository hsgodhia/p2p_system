Input Format
------------
- hostinfo.txt (This file contains host details of all pigs/peers)
  - It contains N lines each line corresponding to a pig/peer. Each line is `<peerId> <addr:port> <hopdelay in milliseconds>`
  - Incase you recieve port conflicts and connection refused errors please edit the port numbers 
  - when running remotely use `/sbin/ifconfig` to get ipaddress

- gameinput.txt (This file is the game input and contains a few sample rounds of the game)
  - The first line is the grid size square length (L)
  - The next line is the number of pillars (P)
  - Then we have the game loop. Enter `n` to continue with a new bird launch, or `y` to quit the game
  - If `n` then for each pig/peer on one line each specify its locations/cordinates in the form of `<peerid> <(x,y)>`
  - The next line indicates the bird launch info `(x_o,y_o) (x_t, y_t) TT HH description(contigous_str)` here, `(x_o, y_o)` is the source of the bird launch, `(x_t, y_t)` is the destination of the bird launch. `TT` is the time to impact, or some what the speed of the bird launch `HH` is the hopcount