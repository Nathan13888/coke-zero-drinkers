from queue import Queue


from em_util import getTargetEdge
from gamelib import debug_write as Print


# DEBUG
import em_log as log

#--------------------------------------
class SimpleQueue:
    def __init__(self):
        self.values = []
    def put(self,val):
        self.values.append(val)
    def get(self):
        return self.values.pop(0) # pop oldest first
    def empty(self):
        return len(self.values)<1
    def length(self):
        return len(self.values)
    def clear(self):
        self.values = []

#--------------------------------------



class PathFinder:
    def __init__(self, game_state):
        self.game_state = game_state
        self.game_map = game_state.game_map
        self.idealness_map_TL = {} # top left
        self.idealness_map_TR = {} # top right
        self.idealness_map_BL = {} # bottom left
        self.idealness_map_BR = {} # bottom right
        self.blockedOnMap = {}
        self.currentTurn = -1
        self.BuildMapBlocks(game_state.game_map)
        self.BuildIdealnessMaps(game_state.game_map)

        self.neighbors = {}

        for point in self.game_map.allLocations:
            self.neighbors[point] = self.GetNeighbors(point)

    #--------------------------------------
    def BuildMapBlocks(self,game_map):
        allLocations = game_map.allLocations
        blocked = self.BlockedOnMap
        for point in allLocations:
            if blocked(point):
                self.blockedOnMap[point] = True
            else:
                self.blockedOnMap[point] = False
    #--------------------------------------
    def GetIdealnessForPoint(self,point, direction):
        idealness = 0
        if direction[0] == 1:
            idealness += point[0]  #bigger to the right
        else:
            idealness += (27 - point[0]) # bigger to the left

        if direction[1] == 1:
            idealness +=  point[1] # bigger on top
        else:
            idealness +=  (27 - point[1]) #bigger on bottom

        return idealness
    #--------------------------------------
    def IdealnessMap(self, pos, dir):
        if dir == [1,1]:
            return self.idealness_map_BR[pos]
        elif dir==[1,-1]:
            return self.idealness_map_TR[pos]
        elif dir==[-1,1]:
            return self.idealness_map_BL[pos]
        return self.idealness_map_TL[pos]
    #--------------------------------------
    def GetIdealnessMap(self,dir):
        if dir == [1,1]:
            return self.idealness_map_BR
        elif dir==[1,-1]:
            return self.idealness_map_TR
        elif dir==[-1,1]:
            return self.idealness_map_BL
        return self.idealness_map_TL
    #--------------------------------------
    def BuildIdealnessMaps(self, game_map):
        for p in game_map.allLocations:
            self.idealness_map_TL[p]=self.GetIdealnessForPoint(p,[-1,-1])
            self.idealness_map_TR[p]=self.GetIdealnessForPoint(p,[ 1,-1])
            self.idealness_map_BL[p]=self.GetIdealnessForPoint(p,[-1, 1])
            self.idealness_map_BR[p]=self.GetIdealnessForPoint(p,[ 1, 1])
    #--------------------------------------
    def GetNeighbors(self, location):
        allLocations = self.game_map.allLocations
        neighbors = ((location[0], location[1] + 1),
                     (location[0], location[1] - 1),
                     (location[0] + 1, location[1]),
                     (location[0] - 1, location[1]))
        return [n for n in neighbors
                if n in allLocations]
    #--------------------------------------
    def BlockedOnMap(self,point):
        if self.game_map[point]:
            return self.game_map[point][0].stationary
        return False
    #--------------------------------------
    def DirectionFromEndPoints(self,end_points):
        map = self.game_map
        x, y = end_points[0]
        direction = [1, 1]
        if x < map.ARENA_SIZE/2:
           direction[0] *= -1
        if y < map.ARENA_SIZE/2:
            direction[1] *= -1
        return direction
    #--------------------------------------
    def GetTargets(self,start,edge = None):
        if edge:
            return self.game_map.get_edge_locations(edge)
        else:
            return self.game_map.get_edge_locations(getTargetEdge(start,self.game_state))
    #--------------------------------------
    def GetPath(self,game_state,start,target = None, recalculateMap = False):
        # update blockedMap
        if game_state.turn_number != self.currentTurn or recalculateMap:
            self.BuildMapBlocks(game_state.game_map)
            self.currentTurn = game_state.turn_number

        self.game_state = game_state
        self.game_map = self.game_state.game_map
       


        # return empty if start point blocked.
        if self.blockedOnMap[tuple(start)]:
            #Print("ERR PATHING: starting tile blocked! {}".format(start))
            return []

        #queue = Queue()
        queue = SimpleQueue()

        PutToQueue = queue.put
        GetFromQueue = queue.get
        QueueIsEmpty = queue.empty





        # get end points if necessary
        if not target:
            targets = [(g[0],g[1]) for g in self.GetTargets(start)]
        else:
            targets = [(g[0],g[1]) for g in self.GetTargets(start,target)]




        idealDirection = self.DirectionFromEndPoints(targets)
        start = tuple(start)
        # get most ideal end point
        most_ideal = start

        PutToQueue(start)
        visited = {}
        visited[start] = 1
        bestIdealness = self.IdealnessMap(start,idealDirection)
        currentIdealness = bestIdealness
        idealnessMap = self.GetIdealnessMap(idealDirection)
        debugIdealnessMap = {}
        debugIdealnessMap[start] = bestIdealness
        BlockedOnMap = self.blockedOnMap


        while not QueueIsEmpty():

            current = GetFromQueue()
            for next in self.neighbors[current]:
                if next in visited or BlockedOnMap[next]:
                    continue
                visited[next] = 1
                currentIdealness = idealnessMap[next]
                if currentIdealness > bestIdealness:
                   bestIdealness = currentIdealness
                   most_ideal = next
                   debugIdealnessMap[next] = currentIdealness
                PutToQueue(next)




        # filter not-reachable targets
        reachable_targets = [(g[0],g[1]) for g in targets if not BlockedOnMap[g]]

        pathLengthMap = {}
        #add best endpoints to queue to find pathlengths
        if most_ideal in reachable_targets:
            for point in reachable_targets:
                PutToQueue(point)
                pathLengthMap[point] = 0
        else:
            PutToQueue(most_ideal)
            pathLengthMap[most_ideal] = 0

        #go through all points and calculate pathlength for each
        while not QueueIsEmpty():
            current = GetFromQueue()
            for next in self.neighbors[current]:
                if  next in pathLengthMap or BlockedOnMap[next]: # don't bother filtering, that wont safe me much time anyways, right?
                    continue

                pathLengthMap[next] = pathLengthMap[current]+1
                PutToQueue(next)


        #get the actual path
        VERTICAL = 1
        HORIZONTAL = 2
        moveDirection = 0 # first step movement

        PutToQueue(start)
        current = start

        pathLength = pathLengthMap[start]

        while not pathLength==0:
            next = self.ChooseNextMove(current,moveDirection,idealDirection,pathLengthMap)
            if current[0] == next[0]:
                moveDirection = HORIZONTAL
            else:
                moveDirection = VERTICAL
            PutToQueue(next)
            current = next
            pathLength = pathLengthMap[next]


        """
        path = [list(elem) for elem in queue.values]
        map = self.GetIdealnessMap(idealDirection)
        log.print("-----------------")
        log.print("starting point: {}".format(start))
        log.print("most ideal: {}".format(most_ideal))
        log.print("ideal direction: {}".format(idealDirection))
        log.print(" ")
        log.print_values_dict(map,game_map)
        log.print(" ")
        log.print_values_dict(pathLengthMap,game_map)
        log.print_path(path,game_map)

        log.print_values_dict(debugIdealnessMap,game_map)
        log.print("ERROR.")


        exit()
        """

        #return dequeued path
        #return [list(elem) for elem in queue.queue]
        return [list(elem) for elem in queue.values]
#--------------------------------------
    def ChooseNextMove(self, current, moveDirection, idealDirection,pathLengthMap):
        BlockedOnMap = self.blockedOnMap
        neighbors = self.neighbors[current]
        neighbors = [n for n in neighbors if not BlockedOnMap[n]]

        bestNext = current
        bestLength = pathLengthMap[current]
        for next in neighbors:
            newBest = False
            length = pathLengthMap[next]

            if length > bestLength:
                continue
            elif length < bestLength:
                newBest = True

            #Filter by direction based on prev move
            if not newBest and not self.BetterDirection(current,next,bestNext,moveDirection,idealDirection):
                continue

            bestNext = next
            bestLength = length
        return bestNext
    #--------------------------------------
    def BetterDirection(self, current, next, bestNext, moveDirection, idealDirection):
        HORIZONTAL = 1
        VERTICAL = 2
        if next == bestNext:
            return False
        if moveDirection == HORIZONTAL and not next[0] == bestNext[0]:
            if current[1] == next[1]:
                return False
            return True
        if moveDirection == VERTICAL and not next[1] == bestNext[1]:
            if current[0] == next[0]:
                return False
            return True
        if moveDirection == 0:
            if current[1] == next[1]:
                return False
            return True

        #To make it here, both moves are on the same axis
        if next[1] == bestNext[1]: #If they both moved horizontal...
            if idealDirection[0] == 1 and next[0] > bestNext[0]: #If we moved right and right is our direction, we moved towards our direction
                return True
            if idealDirection[0] == -1 and next[0] < bestNext[0]: #If we moved left and left is our direction, we moved towards our direction
                return True
            return False
        if next[0] == bestNext[0]: #If they both moved vertical...
            if idealDirection[1] == 1 and next[1] > bestNext[1]: #If we moved up and up is our direction, we moved towards our direction
                return True
            if idealDirection[1] == -1 and next[1] < bestNext[1]: #If we moved down and down is our direction, we moved towards our direction
                return True
            return False
        return True # should never happen ?
    #--------------------------------------
