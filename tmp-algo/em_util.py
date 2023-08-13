import sys
import random
import math
import copy
import gamelib
import queue
#------------------------------------------------------------------
def print_map(game_state_map):
    for y in reversed(range(28)):
        for x in range(28):
            units_at_loc = game_state_map[x,y]
            if units_at_loc:
                sys.stderr.write(units_at_loc[0].unit_type)
            else:
                sys.stderr.write("  ")
        sys.stderr.write("\n")
#------------------------------------------------------------------
def removeDuplicates(list):
    ret = []
    for element in list:
        if element not in ret:
            ret.append(element)
    return ret
#------------------------------------------------------------------
def replaceDeletedEnemyUnits(game_state,history):
    units = [item for item in getDestroyedUnits(game_state,history) if item.player_index==1] # enemy units only
    for unit in units:
        game_state.game_map.add_unit(unit.unit_type,unit.pos,1) #
    return game_state
#------------------------------------------------------------------
def getDestroyedUnits(game_state,history):
    if(len(history))<2:
        return []
    #return removed units

    oldLocs = [x.pos for x in history[-2]]
    newLocs = [x.pos for x in history[-1]]

    destroyedLocs = [x for x in oldLocs if x not in newLocs]

    ret = []
    for unit in history[-2]:
        if unit.pos in destroyedLocs:
            ret.append(unit)
    return ret


    #return [x for x in history[-2] if x not in history[-1]]

    #------------------------------------------------------------------------------
def getNewUnits(game_state,history):
    if(len(history)<2):
        return []
    return [item for item in history[-1] if item not in history[-2]]
#------------------------------------------------------------------------------
def filter_blocked_locations(locations, game_state):
    filtered = []
    for location in locations:
        if not game_state.contains_stationary_unit(location):
            filtered.append(location)
    return filtered
#------------------------------------------------------------------
def filter_empty_locations(locations,game_state):
    return [item for item in locations if game_state.contains_stationary_unit(item)]
#------------------------------------------------------------------------------
def filter_edge_locations(locations,game_state):
    filtered = []
    friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
    for location in locations:
        found = False
        for edge in friendly_edges:
            if location == edge:
                found = True
        if not found:
            filtered.append(location)

    return filtered
#------------------------------------------------------------------------------
# that's not right?
def getAllEdges(game_state):
    return game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
def getEnemyEdges(game_state):
    return game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)
#
def getPlayerEdges(game_state):
    return game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
def getEdgePoints(game_state,index):
    if index==0:
        return getPlayerEdges(game_state)
    else:
        return getEnemyEdges(game_state)
#------------------------------------------------------------------------------
def getEnemyBuildings(game_state):
    locations = getAllLocations(game_state)
    locations = filter_empty_locations(locations,game_state)
    return [item for item in locations if item[1]>13]
#
def getPlayerBuildings(game_state):
    locations = getAllLocations(game_state)
    locations = filter_empty_locations(locations,game_state)
    return [item for item in locations if item[1]<14]

#------------------------------------------------------------------------------
def getAllLocations(game_state):
    all_locations = []
    for i in range(game_state.ARENA_SIZE):
        for j in range(game_state.ARENA_SIZE):
            if (game_state.game_map.in_arena_bounds([i, j])):
                all_locations.append([i, j])
    return all_locations
#------------------------------------------------------------------------------
def buildUnitsAt(unitToBuild,locations,game_state,notBuildAllowed):
    locations = [item for item in locations if item not in notBuildAllowed]
    for location in locations:
        if game_state.can_spawn(unitToBuild, location):
            game_state.attempt_spawn(unitToBuild, location)
#------------------------------------------------------------------
def buildDefenceAround(spot,game_state,type1,type2, notBuildAllowed):
    spots = getPointsAround(spot,game_state)
    spots =  [item for item in spots if game_state.game_map.in_arena_bounds(item)]
    spots =  [item for item in spots if item not in notBuildAllowed]
    count = 0;
    for location in reversed(spots):
        if(count <  len(spots)*0.65):
            if(game_state.can_spawn(type1,location,1)):
                game_state.attempt_spawn(type1, location)
        else:
            game_state.attempt_spawn(type2, location)
        count+=1
#------------------------------------------------------------------
def clearAround(game_state,point):
    points = getPointsAround(point,game_state)
    for point in points:
        game_state.attempt_remove(point)
    #self.notBuildAllowed +=points
    return points
#------------------------------------------------------------------------------
def isClearAround(point,game_state):
    points = getPointsAround(point,game_state)
    points = [item for item in points if game_state.game_map.in_arena_bounds(item)]
    for p in points:
        if game_state.contains_stationary_unit(p):
            return False
    return True

#------------------------------------------------------------------------------
def getValueOfPointsAround(point,game_state):
    pointsAround = getPointsAround(point,game_state)
    score = 0
    for point in pointsAround:
        unit = game_state.game_map[point]
        if unit:
            score += getUnitValue(unit,3,2,-1)
    return score
#------------------------------------------------------------------------------
def getPointsAround(spot,game_state):
    # returns a diagonal pattern
    spots = []
    if spot[0]<14: # point on left side
        x,y=spot
        spots +=[[x-1,y+1]]
        spots +=[[x,y]]
        spots +=[[x+1,y-1]]
        spots +=[[x,y+1]]
        spots +=[[x+1,y]]
        #spots +=[[x+2,y-1]]
    else:
        x,y=spot
        spots +=[[x+1,y+1]]
        spots +=[[x,y]]
        spots +=[[x-1,y-1]]
        spots +=[[x+1,y]]
        spots +=[[x,y-1]]
        #spots +=[[x+2,y+1]]

    #spots = [[spot[0]+i-1,spot[1]+j-1] for j in reversed(range(3)) for i in range(3)]
    return  [item for item in spots if game_state.game_map.in_arena_bounds(item)]
#------------------------------------------------------------------------------
def getPathAround(path,game_state,size):
    ret = []
    min =-size
    max = size+1
    for point in path:
        thisBatch = [[point[0]+x,point[1]+y] for y in range(min,max) for x in range(min,max)]
        thisBatch = [point for point in thisBatch if game_state.game_map.in_arena_bounds(point)]
        ret += thisBatch
    ret = removeDuplicates(ret)
    return ret

#------------------------------------------------------------------
def getTargetEdge(point,game_state):
    left = point[0] < game_state.HALF_ARENA
    bottom = point[1] <  game_state.HALF_ARENA
    right = not(left)
    top = not(bottom)
    if left and bottom:
        return game_state.game_map.TOP_RIGHT
    elif left and top:
        return game_state.game_map.BOTTOM_RIGHT
    elif right and bottom:
        return game_state.game_map.TOP_LEFT
    elif right and top:
        return game_state.game_map.BOTTOM_LEFT
        
#------------------------------------------------------------------
def getUnitValue(unit, dfV, ffV,efV):
    if unit[0].unit_type == 'DF':
        return dfV
    if unit[0].unit_type == 'FF':
        return ffV
    if unit[0].unit_type == 'EF':
        return efV #0 # negative values to actually target encryptors!
    return 0
#------------------------------------------------------------------
def getInformationUnitValue(type,val1,val2,val3):
    if type=="PING":
        return val1
    elif type=="EMP":
        return val2
    elif type =="SCRAMBLER": # ??
        return val3
    return 0
#------------------------------------------------------------------
def predictedTurnsTillDeath(health, lookback):
    if len(health) < 10:
        return 99 # to early to tell
    if lookback > len(health):
        lookback = len(health)

    sinkrate = (health[-lookback] - health[-1]) / lookback
    if sinkrate == 0: # did not take any dmg for the last x turns
        return 99
    return int (health[-1] / sinkrate)
#------------------------------------------------------------------
def getTurnsTillBits(futureBitsFunc, targetBits,player=0):
    turn = 1
    while futureBitsFunc(turn, player) < targetBits:
        turn+=1
    return turn
#------------------------------------------------------------------
def getLastSpawnTurn(history, type):
    count = 0
    for turn in reversed(history):
        for unit in turn:
            if unit[0] == type:
                return count
        count-=1
    return count
#------------------------------------------------------------------
def getDefensePriority(units):
    numSpawns = 0
    avgValuePerSpawn = 0
    numPI = 0
    numEI = 0
    numSI = 0

    # pylint: disable=undefined-variable
    for units in units:
        unitSpawned = False
        if units:
            for unit in units:
                if unit[0]=="PING":
                    numPI+=1
                    unitSpawned = True
                if unit[0]=="EMP":
                    numEI+=1
                    unitSpawned = True
                if unit[0]=="SCRAMBLER":
                    numSI+=1
                    unitSpawned = True
        if unitSpawned:
            numSpawns+=1
    avgPI = 0
    avgEI = 0
    avgSI = 0
    if numSpawns>0:
        avgValuePerSpawn /= numSpawns
        avgPI = numPI / numSpawns
        avgEI = numEI / numSpawns
        avgSI = numSI / numSpawns
    return avgPI, avgEI,avgSI, [avgPI<10,avgPI>9,avgEI<3,avgEI>2,avgSI<10,avgSI>9]
#------------------------------------------------------------------






#------------------------------------------------------------------
# CLASSES
#------------------------------------------------------------------
class BuildQueue:
    def __init__(self):
        self.queue = queue.Queue()
    def reset(self):
        self.queue.queue.clear()
    def push(self,lst):
        self.queue.put(lst)
    def pop(self):
        return self.queue.get()
    def process(self, game_state,notBuildAllowed):
        spawn = game_state.attempt_spawn
        item = []
        if self.queue.full():
            while True:
                item = self.queue.get()
                if item[1] in notBuildAllowed:
                    continue # dont readd if not build allowed here
                if item[0] is None:
                    continue
                unit = spawn(item[0], item[1])
                if unit<1:
                    self.push(item) # re-add if spawning failed?


#------------------------------------------------------------------
class OffenseStrategy:
    def __init__(self):
        self.spawn = []
        self.game_state = None
        self.turnQueue = BuildQueue()
        self.numTurns = 0
    def getTurn(self):
        return self.turnQueue.pop()
    def reset(self):
        self.turns = []
    def plan(self, offense, offenseScore, game_state, turnsTillDeath):
        if not offense:
            return
        if(self.turnQueue.isActive()):
            #gamelib.debug_write("queue active, not planing this turn")
            #gamelib.debug_write(self.turnQueue.active)
            return
        gamelib.debug_write("QUEUE planning new offense")

        self.game_state = game_state
        score = offenseScore.value
        path = offenseScore.path

        bits = game_state.get_resource(game_state.BITS,0)
        cores = game_state.get_resource(game_state.CORES,0)
        futureBits = game_state.project_future_bits
        numberAffordable =  game_state.number_affordable

        costPerUnit = 1
        amount = 0
        cost = 0
        for unit in offense:
            if unit[0]==self.game_state.PING:
                costPerUnit = 1
            elif unit[0] == self.game_state.EMP:
                costPerUnit = 3

            elif unit[0]== self.game_state.SCRAMBLER:
                costPerUnit = 1
            else:
                costPerUnit = 1
            amount+= 1
            cost += costPerUnit

        turns = 0
        if bits >= cost: # can afford on current turn
            turns = 0
        else:
            turns = getTurnsTillBits(futureBits, cost)
            #amount = int(futureBits(turns) / costPerUnit)

        if turns < turnsTillDeath and turns < 10:
            pass
        else:
            amount = int(futureBits(9) / costPerUnit)  # max wait is 9 turns!
            turns = getTurnsTillBits(futureBits, amount )
        self.numTurns = 0

        for turn in range(turns+1):
            self.turnQueue.push([[None,None]])
            self.numTurns+=1
        #self.turnQueue.push([[None,None]])

        for unit in offense:
            self.turnQueue.queue[0].append([unit[0],unit[1]])
            gamelib.debug_write("QUEUE added: {}".format(unit))

        gamelib.debug_write("OFFENSE-STRAT: new offense planned: {}".format(self.numTurns))



    def act(self,game_state,spawnPoint = None):
        self.game_state=game_state
        #gamelib.debug_write("QUEUE length: {}".format(self.NumberOfTurns()))

        self.turnQueue.processUnitQueue(game_state,spawnPoint)
    def active(self):
        return True if self.turnQueue.active else False
    def NumberOfTurns(self):
        return len(self.turnQueue.queue)
#------------------------------------------------------------------
class DefenseStrategy:
    def __init__(self):
        pass
        # set paths for the different offenses..!
        self.leftCannonPath = []
        # etc...
    def get(self,defenseAr, game_state,scores):
        defense = defenseAr[0]
        side = defenseAr[1]
        if defense=="pingCannon":
            #self.clearForType(defense,side)
            return self.deployPingCannon(game_state,side)

        elif defense =="adaptive":
            return self.deployAddaptiveDefense(game_state,scores) # scores == playerScores!?
        elif defense=="maze":
            #self.clearForType(defense,side)
            return self.deployMaze(game_state,side)

    def getAdaptiveDefense(self,game_state,critical,extraCritical,allScores, useBottleNecks=False,useOnlyBottleNecks= False,reversed = False):
        points = []

        if useBottleNecks:
            bottleNecks = self.findBottleNecks(game_state,critical+extraCritical,1)
            for point in bottleNecks:
                points +=[[point, self.coinflip(game_state.DESTRUCTOR,game_state.FILTER,80)]]
            # i actually have No idea how these are sorted??
            points.reverse()
        if useOnlyBottleNecks:
            return points


        scores = extraCritical+critical
        scores = scores[:2]

        for score in scores:
            pointsPath = score.path
            pointsPath.reverse()
            pointsPath = pointsPath[:-4]

            if reversed:
                pointsPath.reverse()

            extendedPath = getPathAround(pointsPath,game_state,1)
            for point in extendedPath:
                    points += [[point,self.coinflip(game_state.DESTRUCTOR,game_state.FILTER,bias = 80)]]
        return points

    def findBottleNecks(self,game_state,scores,width):
        paths = [s.path for s in scores]
        bnPaths = [ getPathAround(path,game_state,width) for path in paths] # does 2 work?
        sets = [set(map(tuple,item)) for item in bnPaths]
        bnPoints = []
        if sets:
            bottlenecks = [item for item in list(set.intersection(*sets)) if item[1]<15] # list of BN points in my half

            if bottlenecks:
                for pos in bottlenecks:
                    if pos[1]>13:
                        continue
                    #bnPoints.append(pos) # PointsAround??
                    bnPoints+=getPointsAround(pos,game_state)
        return bnPoints


    def coinflip(self,item1, item2, bias):
        return item1 if random.randint(0, 100) < bias else item2

    def getPingCannon(self, game_state, side):
        if side == "right":
            points = [[[13+x,x+1],game_state.FILTER] for x in range(-2,15)]
            points += [[[20,9],game_state.ENCRYPTOR],
                       [[21,10],game_state.ENCRYPTOR],
                       [[22,11],game_state.ENCRYPTOR],
                       [[19,8],game_state.ENCRYPTOR]]

            #destructors in front?
            #points +=[[[]]]
        else:
            points = [[[14-x,x+1],game_state.FILTER] for x in range(-2,15)]
            points += [[[7,9],game_state.ENCRYPTOR],
                       [[6,10],game_state.ENCRYPTOR],
                       [[5,11],game_state.ENCRYPTOR],
                       [[8,8],game_state.ENCRYPTOR]]
        return points

    def removePingCannon(self, game_state, side):
        points =[p[0] for p in self.getPingCannon(game_state, side)]
        removed = game_state.attempt_remove(points)
        return removed

    def checkIfBuilt(self,type,side,game_state):


        game_map = game_state.game_map
        if type=="pingCannon":
            points = []
            if side=="left":
                points = [[14-x,x+1] for x in range(-2,15)]
            else:
                points = [[13+x,x+1] for x in range(-2,15)]
            points = [p for p in points if game_map.in_arena_bounds(p)]

            missing = 0
            for pos in points:
                if game_map[pos]:
                    if not game_map[pos][0].stationary:
                        missing += 1
                else:
                    missing += 1
            return missing

        elif type=="maze":
            points =[p[0] for p in self.getMaze(game_state, side)]

            missing = 0
            for pos in points:
                if game_map[pos]:
                    if not game_map[pos][0].stationary:
                        missing += 1
                else:
                    missing += 1
            return missing



        return -1




    def removeMaze(self,game_state,side):
        points = [p[0] for p in self.getMaze(game_state,side)]
        removed = game_state.attempt_remove(points)
        return removed

    def getMaze(self, game_state, side):
        points = []
        #gamelib.debug_write("returning maze for ({}) side".format(side))
        side = "left" # LOL TODO
        if side == "left":
            #points += [[[x,13], game_state.FILTER] for x in range(3,28)]
            points +=[[[x,11], game_state.DESTRUCTOR] for x in range(3,26,4)]
            points +=[[[0,13],game_state.DESTRUCTOR],
                      [[27,13],game_state.DESTRUCTOR],
                      [[1,12],game_state.DESTRUCTOR],
                      [[26,12],game_state.DESTRUCTOR],
                      [[25,11],game_state.DESTRUCTOR],
                      [[2,11],game_state.DESTRUCTOR],
                      [[3,10],game_state.DESTRUCTOR],
                      [[4,9],game_state.DESTRUCTOR],
                      [[1,13],game_state.DESTRUCTOR],
                      [[26,13],game_state.DESTRUCTOR]]

            points +=[[[x,11],game_state.FILTER] for x in reversed(range(8,26))]
            points +=[[[x,13],game_state.FILTER] for x in range(0,24)]
            points +=[[[x,10],game_state.ENCRYPTOR] for x in range(20,25)]
            #else:
                #points += [[[x,13], game_state.FILTER] for x in range(0,26)]

        return points






    def getNotBuildAllowedByCannon(self,side):
        points = []
        if side == "right":
            points =  [[13+x,x-1] for x in range(-2,15)]
            points += [[13+x,x+0] for x in range(-2,15)]
        else:
            points = [[14-x,x-1] for x in range(-2,15)]
            points +=[[14-x,x+0] for x in range(-2,15)]
        return points
    def getNotBuildAllowedByMaze(self,side):
        if side=="left":
            return [[24, 13], [25, 13], [3, 12], [4, 12], [5, 12], [6, 12], [7, 12], [8, 12], [9, 12], [10, 12], [11, 12], [12, 12], [13, 12], [14, 12], [15, 12], [16, 12], [17, 12], [18, 12], [19, 12], [20, 12], [21, 12], [22, 12], [23, 12], [24, 12], [25, 12], [4, 11], [5, 11], [5, 10], [6, 10], [6, 9], [7, 9], [7, 8], [8, 8], [6, 7], [7, 7], [8, 7], [9, 7]]
        else:
            return [[25,12],[26,12],[26,13],[27,13]]

    def clearForType(self,game_state,type,side):
        delete = []
        remove = game_state.attempt_remove
        notAllowed = []
        if type == "pingCannon" :
            #keep = [point[0] for point in self.getPingCannon(game_state,side)]
            #delete = [point for point in getPlayerBuildings(game_state) if point not in keep]
            notAllowed = self.getNotBuildAllowedByCannon(side)
            delete = notAllowed
            if side=="right":
                delete = [item for item in delete if item[0]>12]
            else:
                delete = [item for item in delete if item[0]<15]

        elif type == "maze" :
            notAllowed = self.getNotBuildAllowedByMaze(side)
            delete = notAllowed
        removed = 0
        if delete:
            removed = remove(delete)
        gamelib.debug_write("REMOVING {} units".format(removed))
        return notAllowed, removed == 0 # not build allowed!
    # I somehow need to get the path for this to work...^^
    def pathIsClear(self,path,game_state):
        map = game_state.game_map
        for x,y in path:
            if map[x][y]:
                return False
        return True
