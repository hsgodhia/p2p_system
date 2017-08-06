The following things are some scope of improvements and limitations:

1. We leave it up to the user to ensure that all pigs are initialized with different locations, although we prevent any two pigs moving into the same empty space during an evasion

2. We leave it up to the user to ensure that pig locations are different from pillar locations and that the input cordinates and locations are within the boundary of the grid, although when making an evasive action and moving we ensure that
 - the pigs next moves are valid,
 - within boundary, 
 - don't collide and
 - are not one of the pillars

 3. We support a 2D square playground or square grid which can be extend to 3D in future

 4. We currently have static pillars this can be extended to have pillars as processes too

 5. The pigs erase state after every round, leaving it to the game driver to track scores. This can be extended to have stateful peers

 6. To support multiple bird launches at a single time, currently one launch per round