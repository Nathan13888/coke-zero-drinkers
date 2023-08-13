"""
base algo:
https://www.redblobgames.com/pathfinding/a-star/implementation.html
"""
import heapq
import em_log as log

#--------------------------------------
class PriorityQueue:
    def __init__(self):
        self.elements = []
    def empty(self):
        return len(self.elements) == 0
    def put(self, item, priority):
        #self.elements.append(item)
        heapq.heappush(self.elements, (priority, item))
    def get(self):
        #return self.elements.pop()
        return heapq.heappop(self.elements)[1]
    def decay(self):
        self.elements = [(e[0]+7,e[1]) for e in self.elements]



#--------------------------------------

def heuristic(a, thisDir, nextDir, targetDir, length, map):

    # punish moving in the same direction again
    mod1 = 1
    if thisDir == nextDir:
        mod1 = 5


    mod2=1
    # extra punish if we go against our target direction
    # /only/ go back if we have to!
    if nextDir[0]!=targetDir[0] and nextDir[1]!=targetDir[1]:
        mod2 = 1500

    # get idealness (smaller -> more ideal)
    idealness = 0
    if targetDir[0] == -1:
        idealness +=  a[0]
    else:
        idealness +=  (27 - a[0])
    if targetDir[1] == -1:
        idealness += a[1]
    else:
        idealness += (27 - a[1])
    idealness/=(27) # "normalize" idealness

    return 1 + idealness * mod1 * mod2
#--------------------------------------
def PathBlocked(pos,targetDir,map):
    if(targetDir[1]==1) :#and mod1 == 1):
        if map[[pos[0],pos[1]+1]]: # blocked
            return True

    elif(targetDir[1]==-1 ):#and mod1 == 1):
        if map[[pos[0],pos[1]-1]]: # blocked
            return True

    if(targetDir[0]==1) :#and mod1 == 1):
        if map[[pos[0]+1,pos[1]]]: # blocked
            return True

    elif(targetDir[0]==-1 ):#and mod1 == 1):
        if map[[pos[0]-1,pos[1]]]: # blocked
            return True
    return False
#--------------------------------------
def SmallestDistance(a,lst):
    return sorted([Distance(a,p) for p in lst])[0]
#--------------------------------------
def Distance(a,b):
    return (a[0]-b[0])**2 + (a[1]-b[1])**2
#--------------------------------------
def DirectionFromEndPoints(map, end_points):
    x, y = end_points[0]
    direction = [1, 1]
    if x < map.ARENA_SIZE/2:
       direction[0] *= -1
    if y < map.ARENA_SIZE/2:
        direction[1] *= -1
    return direction
#-------------------------------------
def FindDeepestValey(game_map,goals,idealDirection):
    if idealDirection == [1,1]: # top right
        # TODO: figure out the right sorting for each direction..!
        for y in reversed(range(0,28)):
            for x in reversed(range(0,28)):
                if((x,y) in game_map.allLocations):
                    if not game_map[[x,y]]:
                        log.print("found top right target point: {}".format((x,y)))
                        return [(x,y)]
    if idealDirection == [1,-1]: # bottom right
        # TODO: figure out the right sorting for each direction..!
        for y in (range(0,28)):
            for x in reversed(range(0,28)):
                if((x,y) in game_map.allLocations):
                    if not game_map[[x,y]]:
                        log.print("found bottom right target point: {}".format((x,y)))
                        return [(x,y)]
    if idealDirection == [-1,1]: # top left
        # TODO: figure out the right sorting for each direction..!
        for y in reversed(range(0,28)):
            for x in (range(0,28)):
                if((x,y) in game_map.allLocations):
                    if not game_map[[x,y]]:
                        log.print("found top left target point: {}".format((x,y)))
                        return [(x,y)]
    if idealDirection == [-1,-1]: # bottom left
        # TODO: figure out the right sorting for each direction..!
        for y in (range(0,28)):
            for x in (range(0,28)):
                if((x,y) in game_map.allLocations):
                    if not game_map[[x,y]]:
                        log.print("found bottom right target point: {}".format((x,y)))
                        return [(x,y)]

    #riiiiight?^^
    return []



#--------------------------------------
def em_a_star_search(game_map, start, goals): # goals needs to be filtered for blocked elements asap
    if game_map[start]:
        return []

    frontier = PriorityQueue()
    putToQueue = frontier.put
    getFromQueue = frontier.get
    queueIsEmpty = frontier.empty

    #log.print("pathing started")
    endpoints = [(g[0],g[1]) for g in goals if not game_map[g]]



    start = tuple(start)



    putToQueue(start, 0) # first value in queue

    came_from = {}
    cost_so_far = {}
    dir = {}
    length_so_far = {}
    blocked = {}
    came_from[start] = None
    cost_so_far[start] = 1
    length_so_far[start] = 1
    dir[start] = DirectionFromEndPoints(game_map, goals)
    dir[start][1]=0
    mod = 1
    idealDirection = DirectionFromEndPoints(game_map,goals)

    nextDir = (0,0)
    next_cost = 0
    if not endpoints:
        endpoints = FindDeepestValey(game_map,goals,idealDirection)




    while not queueIsEmpty():
        current = getFromQueue()
        #log.print("{} / {}".format(current,endpoints))
        if current in endpoints:
            log.print("reached end, {}".format(current))
            break

        # decay the queue - look at "junger" elements first!
        frontier.decay() # only once per node
        # i actually need to update cost_so_far aswell : /
        # that's actually not true! ... for some reason.
        #for element in frontier.elements:
        #    cost_so_far[element[1]] = element[0] # like this?


        for next in get_neighbors(current,game_map):

            nextDir = get_dir(current,next)
            #next_cost = cost_so_far[current] + heuristic(next, idealDirection) * mod * len(came_from)

            next_cost = cost_so_far[current] + heuristic(next,
                                                         dir[current],
                                                         nextDir,
                                                         idealDirection,
                                                         length_so_far[current],
                                                         game_map)

            if next not in cost_so_far or next_cost < cost_so_far[next]: # not calculated or new best
                dir[next]=nextDir
                length_so_far[next] = length_so_far[current]+1
                cost_so_far[next] = next_cost

                putToQueue(next, next_cost) # * (1 if dir[next][0]!=0 else 2))
                came_from[next] = current

    # DEBUG:

    log.print("startpoint: {}".format(start))
    log.print("startdir:   {}".format(dir[start]))
    log.print("dir:  {}".format(idealDirection))
    #log.print("goal: {}".format(goals[0]))

    log.print_values_dict(cost_so_far,game_map)

    return reconstruct_path(came_from, start, current,dir) # do this if we found a path to the end

    # else: ... do something else?^^
    # maybe make the goals the deepest valey if i don't have a target point? > this could work!


#--------------------------------------
def get_dir(current, next):
    ret = [0,0]
    if next[0]<current[0]:
        ret[0] = -1
    if next[0]>current[0]:
        ret[0] = 1
    if next[1]<current[1]:
        ret[1] = -1
    if next[1]>current[1]:
        ret[1] = 1

    return ret;#return [b[0]-a[0],b[1]-a[1]]
#--------------------------------------


    # TODO: argh, wie geht des jetz' wieder?^^
#--------------------------------------
# move to map?
def get_neighbors(location, game_map):
    allLocations = game_map.allLocations
    neighbors = ((location[0], location[1] + 1),
                 (location[0], location[1] - 1),
                 (location[0] + 1, location[1]),
                 (location[0] - 1, location[1]))

    return (n for n in neighbors if n in allLocations and not game_map[n])
#--------------------------------------
def reconstruct_path(came_from, start, goal,dir):
    current = goal
    path = []

    while current != start:
        #log.print(dir[current])
        path.append(list(current))
        current = came_from[current]
    path.append(list(start)) # optional
    path.reverse() # optional
    return path
#--------------------------------------
