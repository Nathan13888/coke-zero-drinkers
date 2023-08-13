import gamelib # used for debug_write
import random # used for coinflip
import em_log as log # for dict-printing
from typing import Literal

"""
building plans for predefined layouts based on turnNumber
"""

"""
#---------------------------------------------------------------
UNIT COST:
- ping: 1
- emp: 3
- filter: 1
- destructor: 6 # o. O
- encryptor: 4
#---------------------------------------------------------------
UNIT DAMAGE
- ping: 2
- emp: 8
- destructor: 16 # o. O
#---------------------------------------------------------------
UNIT HEALTH
- ping: 15
- emp: 5
- filter: 60
- destructor: 75
#---------------------------------------------------------------
"""




#---------------------------------------------------------------
# MAZE
#---------------------------------------------------------------
def GetMaze(game_state):

    points = []
    # basic defense:
    points += [[[2,13],game_state.DESTRUCTOR],
              [[25,13],game_state.DESTRUCTOR],
              [[8 ,11],game_state.DESTRUCTOR],
              [[19,11],game_state.DESTRUCTOR],
              [[13,11],game_state.DESTRUCTOR]]

    #decoy
    points += [[[ 3,13],game_state.FILTER]]
    points += [[[24,13],game_state.FILTER]]

    points += [[[ 7,11],game_state.FILTER]]
    points += [[[ 9,11],game_state.FILTER]]

    points += [[[12,11],game_state.FILTER]]
    points += [[[14,11],game_state.FILTER]]

    points += [[[18,11],game_state.FILTER]]
    points += [[[20,11],game_state.FILTER]]


    if game_state.turn_number < 5:
        return points
    else:
        points +=[[[26,12],game_state.DESTRUCTOR],
                  [[23,11],game_state.DESTRUCTOR],
                  [[0,13],game_state.DESTRUCTOR]]


        points +=[[[x,11],game_state.FILTER] for x in reversed(range(4,26))]
        points +=[[[x,13],game_state.FILTER] for x in range(0,26)]

        points +=[[[x,9],game_state.ENCRYPTOR] for x in reversed(range(18,24))]

        return points

#---------------------------------------------------------------
def RemoveMaze(game_state):
    points = [p[0] for p in GetMaze(game_state)]
    removed = game_state.attempt_remove(points)
    return removed
#---------------------------------------------------------------
def GetNotBuildAllowedByMaze(game_state):
    if game_state.turn_number < 5:
        return []
    return [[24, 13], [25, 13], [3, 12], [4, 12], [5, 12], [6, 12], [7, 12], [8, 12], [9, 12], [10, 12], [11, 12], [12, 12], [13, 12], [14, 12], [15, 12], [16, 12], [17, 12], [18, 12], [19, 12], [20, 12], [21, 12], [22, 12], [23, 12], [24, 12], [25, 12], [4, 11], [5, 11], [5, 10], [6, 10], [6, 9], [7, 9], [7, 8], [8, 8], [6, 7], [7, 7], [8, 7], [9, 7]]
    # TODO: we sure that's correct!??
#---------------------------------------------------------------
def GetMazeSpawn():
    return [20,6]
#---------------------------------------------------------------
def GetMinCoresForMaze():
    return 20 # VALUE




#---------------------------------------------------------------
# PING CANNON
#---------------------------------------------------------------
def GetMinCoresForPingCannon():
    """
    cost:
    13*1 filter = 13
    4-5*4 ENC = 16 - 20

    33 to build the full thing? that can't be right!? [o. O]

    cannon +
    1 enc: 17
    2 enc: 21
    3 enc: 25
    4 enc: 29
    5 enc: 33
    """
    return 25
#---------------------------------------------------------------
def GetPingCannon(game_state, side: Literal["left", "right"]):
    if side == "right":
        points = [[[13+x,x+1],game_state.FILTER] for x in range(-2,15)]
        points += [[[16,5],game_state.ENCRYPTOR],
                   [[17,6],game_state.ENCRYPTOR],
                   [[18,7],game_state.ENCRYPTOR],
                   [[19,8],game_state.ENCRYPTOR],
                   [[20,9],game_state.ENCRYPTOR]]
    else:
        points = [[[14-x,x+1],game_state.FILTER] for x in range(-2,15)]
        points += [[[11,5],game_state.ENCRYPTOR],
                   [[10,6],game_state.ENCRYPTOR],
                   [[9, 7],game_state.ENCRYPTOR],
                   [[8, 8],game_state.ENCRYPTOR],
                   [[7, 9],game_state.ENCRYPTOR]]

    points = [u for u in points if game_state.game_map.in_arena_bounds(u[0])]
    return points
#---------------------------------------------------------------
def GetPingCannonSpawn(side):
    if side == "right": # that's a bit odd?
        return [13,0]
    else:
        return [14,0]
#---------------------------------------------------------------
def RemovePingCannon(game_state, side):
    #points =[p[0] for p in GetPingCannon(game_state, side)]
    # only remove filters?
    points =[p[0] for p in GetPingCannon(game_state, side)] # if p[1] == game_state.FILTER]

    removed = game_state.attempt_remove(points)
    return removed
#---------------------------------------------------------------
def GetNotBuildAllowedByCannon(side):
    points = []
    if side == "right":
        points =  [[13+x,x-1] for x in range(-2,15)]
        points += [[13+x,x+0] for x in range(-2,15)]
    else:
        points = [[14-x,x-1] for x in range(-2,15)]
        points +=[[14-x,x+0] for x in range(-2,15)]
    return points




#---------------------------------------------------------------
# ADAPTIVE DEVENSE
#---------------------------------------------------------------
def GetAdaptiveDefense_old(game_state, game_grid,player,enemy, useBottleNecks=False, useOnlyBottleNecks= False, reversed = False ):
    units = []

    if useBottleNecks:
        bottleNecks = FindBottleNecks(game_state,enemy.critical,1)
        for point in bottleNecks:
            units +=[[point, CoinFlip(game_state.DESTRUCTOR,game_state.FILTER,80)]]
        # i actually have No idea how these are sorted??
        units.reverse()
    if useOnlyBottleNecks:
        return units


    scores =  enemy.critical
    scores = scores[:2] # only use 2 most critical pathes
    notBuildAllowed = []
    for score in scores:
        #pointsPath = score.path
        pointsPath = [p for p in score.path if p[1]<14] # skip enemy points

        if not reversed:
            pointsPath.reverse() # end points of path first!

        pointsPath = pointsPath[:4]  # only use last couple of points


        extendedPath = GetPathAround(pointsPath,game_state,1)
        extendedPath = RemoveDuplicates(extendedPath)

        # maybe don't shorten beforehand,
        # but get all possible points,
        # then filter for already built ones,
        # and only then limit them to x per path?
        # for this i'd need gamegrid I think?
        # or just build ONLY around most critical? - as this is also the most likely to be picked?
        # ... ?

        for point in extendedPath:
                units += [[point,CoinFlip(game_state.DESTRUCTOR,game_state.FILTER,bias = 60)]]
        notBuildAllowed += [p for p in score.path if p[0]>5 and p[0]<22]

    return units, notBuildAllowed
#---------------------------------------------------------------
def GetAdaptiveDefense_working(game_state,game_grid,player, enemy, useBottleNecks=False, reversed = False ):
    units = []
    useBottleNecks = True
    if useBottleNecks:
        bottleNecks = FindBottleNecks(game_state,enemy.critical,2)
        # bottlenecks: 
        # points on the field where ALL enemy paths get close to!
        # could be a good idea to build destructors there?
        # TODO: use bottleNecks!   
        if bottleNecks:
            units +=[[[bottleNecks[0][0],bottleNecks[0][1]],game_state.DESTRUCTOR]]
            units +=[[[bottleNecks[0][0]+1,bottleNecks[0][1]],game_state.FILTER]]
            units +=[[[bottleNecks[0][0]-1,bottleNecks[0][1]],game_state.FILTER]]
            units +=[[[bottleNecks[0][0],bottleNecks[0][1]-1],game_state.DESTRUCTOR]]


    scores =  enemy.critical
    scores = scores[:1] # only use most critical pathes
    notBuildAllowed = []
    for score in scores:
        pointsPath = [p for p in score.path if p[1]<14] # skip enemy points
        if not reversed:
            pointsPath.reverse() # end points of path first!

        if score.endPoint[0]<3:
            units = GetCornerBlockade(game_state,"left")
        elif score.endPoint[0]>24:
            units = GetCornerBlockade(game_state,"right")
        
            notBuildAllowed += [p for p in score.path if p[0]>5 and p[0]<22]
            gamelib.debug_write("CORNER DEFENSE")
        else:
            notBuildAllowed += [p for p in score.path if p[0]>5 and p[0]<22]
            heatmap = {}
            width = 1
            for x,y in pointsPath[:5]:
                for a in range(-width,width+1):
                    for b in range(-width,width+1):
                        p = (x+a,y+b)
                        if list(p) in pointsPath:
                            continue
                        if p in heatmap:
                            heatmap[p] +=1
                        else:
                            heatmap[p] = 1

            actionPoints = [ [list(k),v] for k, v in heatmap.items() ]
            #gamelib.debug_write(actionPoints)
            for heatmapPoint in actionPoints:
                if heatmapPoint[1]>1:
                    units += [[heatmapPoint[0], game_state.FILTER]]
                else:
                    units += [[heatmapPoint[0], game_state.DESTRUCTOR]]

    return units, notBuildAllowed
#---------------------------------------------------------------
def GetAdaptiveDefense(game_state, gameGrid,player, enemy, useBottleNecks=False, reversed = False ):
    
    #FIRST:
    #test if enemy attacks corner, and if: spawn cornerblock!
    
    #else:
    #    everything else.
    if enemy.AttacksCorner():
        if enemy.bestScore.endPoint[0]<14:
            units = GetCornerBlockade(game_state,"left")
            return units, []
        elif enemy.bestScore.endPoint[0]>13:
            units = GetCornerBlockade(game_state,"right")
            return units, []


    heatmap = {} 
    points = []

    for pos in game_state.game_map.allLocations:
        if gameGrid[pos].active and gameGrid[pos].playerIndex==0 and gameGrid[pos].type == game_state.DESTRUCTOR:
                points += GetPointsAround(pos,game_state,2)

    for p in points:
        if p[1]<14:
            if p in heatmap:
                heatmap[p] += 1 
            else: 
                heatmap[p] = 1

    for pos in game_state.game_map.allLocations:
        if not pos in heatmap and pos[1]<14:
            heatmap[pos] = 0
    for pos in enemy.bestScore.path:
        if tuple(pos) in heatmap:
            heatmap[tuple(pos)]-=1

    #log.print_values_dict(heatmap,game_state.game_map,scaling = False)

    heatmapPoints = [ [k,v] for k, v in heatmap.items() if list(k) in GetPathAround(enemy.bestScore.path,game_state,1)] # does this make sense?
    heatmapPoints.sort(key=lambda x:x[1], reverse=True) # lowest defended points first!
    
    #log.print(heatmapPoints)
    coresToSpend = player.cores
    #if player.bits>=10:
    coresToSpend-= 3 * game_state.type_cost(game_state.ENCRYPTOR)

    log.print("cores to spend: {}".format(coresToSpend))

    coresSpent = 0 
    units = []
    while coresSpent + 8 < coresToSpend and heatmapPoints:
        point = heatmapPoints.pop()
        u,c = GetDefenseBlock(game_state,point[0],units,enemy,player)
        units += u
        coresSpent+=c
        if c>0:
            log.print("ADDING BLOCK AT {}".format(point[0]))
    #log.print(units)
    return units, []

#---------------------------------------------------------------
def GetCornerBlockade(game_state,side):
    units = []
    log.print("CORNER BLOCKADE")
    if side=="left":
        #units.append([[0,13],game_state.FILTER])
        #units.append([[1,12],game_state.DESTRUCTOR])
        #units.append([[2,13],game_state.DESTRUCTOR])
        #units.append([[3,13],game_state.DESTRUCTOR])
        #units.append([[2,11],game_state.DESTRUCTOR])
        
        units.append([[0,13],game_state.FILTER])
        units.append([[1,13],game_state.FILTER])
        units.append([[2,13],game_state.FILTER])
        units.append([[3,13],game_state.FILTER])
        units.append([[1,12],game_state.DESTRUCTOR])
        units.append([[2,12],game_state.DESTRUCTOR])
        units.append([[4,13],game_state.DESTRUCTOR])
        units.append([[3,12],game_state.DESTRUCTOR])
        units.append([[2,11],game_state.DESTRUCTOR])
        
        # first row: filters + maybe a destructor
        # second row: destructors
        # third row: destructors

    elif side == "right":
        #units.append([[27,13],game_state.FILTER])
        #units.append([[26,12],game_state.DESTRUCTOR])
        #units.append([[25,13],game_state.DESTRUCTOR])
        #units.append([[24,13],game_state.DESTRUCTOR])
        #units.append([[25,11],game_state.DESTRUCTOR])
        
        units.append([[27,13],game_state.FILTER])
        units.append([[26,13],game_state.FILTER])
        units.append([[25,13],game_state.FILTER])
        units.append([[24,13],game_state.FILTER])
        units.append([[26,12],game_state.DESTRUCTOR])
        units.append([[25,12],game_state.DESTRUCTOR])
        units.append([[23,13],game_state.DESTRUCTOR])
        units.append([[24,12],game_state.DESTRUCTOR])
        units.append([[25,11],game_state.DESTRUCTOR])
        
    return units
#---------------------------------------------------------------
def GetMovementDirection(a,b):
    return [a[0]-b[0],a[1]-b[1]] #?
#---------------------------------------------------------------
def FindBottleNecks(game_state, scores, width):
    paths = [s.path for s in scores]
    bnPaths = [ GetPathAround(path,game_state,width) for path in paths] # does 2 work?
    pathSets = [set(map(tuple,item)) for item in bnPaths]
    bottlenecks = []
    if pathSets:
        bottlenecks = [list(item) for item in list(set.intersection(*pathSets)) if item[1]<12] # list of BN points in my half

    return bottlenecks
#---------------------------------------------------------------
def GetDefenseBlock(game_state, pos, units,enemy,player):
    # cost for 1 block is: 9 cores.

    # todo: only return points if I actually build the block there!
    points = [(pos[0]+1,pos[1]-1), 
              (pos[0]-1,pos[1]-1), 
              (pos[0]  ,pos[1]-1), 
              (pos[0]  ,pos[1]  )]

    # check for planned units
    for u in units:
        if tuple(u[0]) in points:
            return [], 0
    # check for units on board:
    for point in points:
        if (game_state.contains_stationary_unit(point) or 
            #list(point) in enemy.bestScore.path or 
            list(point) in player.bestScore.path or 
            point[1] > 13): # or point not in game_state.game_map.allLocations:
            return [], 0

    # everything is good to go:


    units = []
    units.append([[pos[0],pos[1]],game_state.DESTRUCTOR])
    units.append([[pos[0]+1,pos[1]],game_state.FILTER])
    units.append([[pos[0]-1,pos[1]],game_state.FILTER])
    units.append([[pos[0],pos[1]+1],game_state.FILTER])
    return units, 9 #(cost)
#---------------------------------------------------------------
def CoinFlip(item1, item2, bias):
    return item1 if random.randint(0, 100) < bias else item2
#---------------------------------------------------------------
def GetPathAround(path,game_state,size):
    ret = []
    min =-size
    max = size+1
    for point in path:
        thisBatch = [[point[0]+x,point[1]+y] for y in range(min,max) for x in range(min,max)]
        thisBatch = [point for point in thisBatch if game_state.game_map.in_arena_bounds(point)]
        ret += thisBatch
    ret = RemoveDuplicates(ret)
    return ret
#---------------------------------------------------------------
def GetPointsAround(spot,game_state,width):
    spots = []
    for x in range(-width,width+1):
        for y in range(-width,width+1):
            spots.append((spot[0]+x,spot[1]+y))
    
    return  [item for item in spots if item in game_state.game_map.allLocations]
#------------------------------------------------------------------
def RemoveDuplicates(list):
    ret = []
    for element in list:
        if element not in ret:
            ret.append(element)
    return ret

#---------------------------------------------------------------
# UTILITY
#---------------------------------------------------------------

#returns cost of units that still need to be built!
def CheckIfBuilt(game_state,type,side: Literal["left", "right"] = "left"):
    game_map = game_state.game_map

    cost = 0


    if type=="pingCannon":
        units = GetPingCannon(game_state,side)[:-2] # ignore last two ENCs...

        for unit in units:
            found = False
            if game_map[unit[0]]:
                if game_map[unit[0]][0].stationary:
                    found = True
            if not found:
                cost += game_state.type_cost(unit[1])

        return cost

    elif type=="maze":
        units = GetMaze(game_state)
        for unit in units:
            found = False
            if game_map[unit[0]]:
                if game_map[unit[0]][0].stationary:
                    found = True
            if not found:
                cost += game_state.type_cost(unit[1])
        return cost
    return -1

#---------------------------------------------------------------


def ClearForType(game_state,type,side = "left"):
    delete = []
    remove = game_state.attempt_remove
    notAllowed = []
    if type == "pingCannon" :
        notAllowed = GetNotBuildAllowedByCannon(side)
        delete = notAllowed
        if side=="right":
            delete = [item for item in delete if item[0]>12]
        else:
            delete = [item for item in delete if item[0]<15]

    elif type == "maze" :
        notAllowed = GetNotBuildAllowedByMaze(game_state)
        delete = notAllowed
    removed = 0
    if delete:
        removed = remove(delete)
    #gamelib.debug_write("REMOVING {} units to clear for {}".format(removed,type))
    return notAllowed, removed == 0 # not build allowed!

#---------------------------------------------------------------
def GetRefundAmount(game_state, points):
    refund = 0
    for point in points:
        if game_state.contains_stationary_unit(point):
            #type = game_state.game_map[point][0].type
            cost = game_state.game_map[point][0].cost
            health = game_state.game_map[point][0].stability
            originalHealth = game_state.game_map[point][0].max_stability
            refund += 0.75*cost*(health/originalHealth)
    return refund
