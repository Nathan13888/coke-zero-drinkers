import gamelib
from gamelib import debug_write
import sys
from math import sqrt
#------------------------------------------------------------------
# UNIT
import em_util
#------------------------------------------------------------------
class Unit:
    def __init__(self,pos):
        self.health = [0]
        self.age = -99999
        self.pos = pos
        self.type = ""
        self.playerIndex = -1
        self.active = False
        self.neighbors = None
        self.score = -1
        self.value = 0
        self.range = 0
    #-----------------------------------
    def update(self,health):
        if not self.active:
            return
        self.health += [health]
        self.age+=1
        if health <=0:
            self.delete()
    #-----------------------------------
    def spawn(self,unit):
        self.health = [unit.stability]
        self.age = 1
        self.pos = unit.pos
        self.type = unit.unit_type
        self.playerIndex = unit.player_index
        self.active = True
        self.value = self.getValue()
        self.range = self.getRange()
    #-----------------------------------
    def delete(self):
        self.health = []
        self.age = -9999
        self.type =""
        self.playerIndex = -1
        self.active = False
        self.value = 0
    #-----------------------------------
    def avgLossPerTurn(self,lookback):
        if not self.active:
            return 0
        if lookback>self.age:
            lookback=self.age
        return (self.health[-lookback]-self.health[-1])/lookback
    #-----------------------------------
    def turnsTillDeath(self):
        if not self.active:
            return 0
        if self.avgLossPerTurn(4)==0:
            return 100
        return self.health[-1]/self.avgLossPerTurn(4)
    #-----------------------------------
    def getValue(self):
        if self.type == "DF":
            return 1
        elif self.type == "FF":
            return 0 # do not consider filters? -> i won't take dmg from them so it "should" be correct, yes?
        elif self.type == "EF" : # don't consider enemy encs
            return -0.1 # VALUE
        return 0
    #-----------------------------------
    def getRange(self):
        if self.type == "DF":
            return 3
        elif self.type == "FF":
            return 0 # do not consider filters? -> i won't take dmg from them so it "should" be correct, yes?
        elif self.type == "EF" : # don't consider enemy encs
            return 3 # VALUE
    #-----------------------------------
    def getNeighbors(self):
        #debug_write([n.pos for n in self.neighbors if not n.active])
        # why not return self.neighbors # ???
        return self.neighbors
        #return [n for n in self.neighbors]
#------------------------------------------------------------------
# GAME GRID
#------------------------------------------------------------------
class GameGrid:
    def __init__(self,game_map):
        self.allLocations = self.get_all_locations()


        self.map = {}
        for pos in self.allLocations:
            self.map[pos] = Unit(pos)
      
        #set neighbors
        for x, y in self.allLocations:
            neighbors = ((x + 1, y), (x-1, y), (x, y+1), (x, y-1))
            neighbors = [(x,y) for x,y in neighbors if (x,y) in self.allLocations]
            self.map[(x,y)].neighbors = neighbors

        self.unitsAround = {}
    #-----------------------------------
    def __getitem__(self, pos):
        return self.map[tuple(pos)]
    #-----------------------------------
    def __iter__(self):
        self.__start = 0
        return self
    #-----------------------------------
    # this allows for "for pos in gameMap:"
    # but why not return units?
    def __next__(self):
        location = self.allLocations[self.__start]
        if location == self.allLocations[-1]:
            raise StopIteration
        self.__start +=1
        return location
    #-----------------------------------
    def getUnitMap(self):
        map = {}
        for pos in self.allLocations:
            if self.map[pos].active:
                map[pos] = self.map[pos].playerIndex 
        return map
    #-----------------------------------
    def update(self,game_map):
        #gridChanged = False
        self.unitsAround.clear() # only do that if the grid changed?

        # update previous units
        for pos in self.allLocations:
            unit = self.map[pos]
            if game_map[unit.pos]:
                unit.update(game_map[unit.pos][0].stability)
            else:
                unit.delete()
                #gridChanged = True

        # add new units:
        for pos in self.allLocations:
            if game_map[pos]:
                if not game_map[pos][0].stationary:
                    continue
                if not self.map[pos].active:
                    self.map[pos].spawn(game_map[pos][0])
                    #gridChanged = True

        #if gridChanged:
        #    self.unitsAround.clear() # only do that if the grid changed?
        #    debug_write("unitsAround-dict cleared")
    #-----------------------------------
    def addUnit(self,type,pos):
        pass
    #-----------------------------------
    def removeUnit(self,pos):
        self.map[tuple(pos)].delete()
    #-----------------------------------
    def HasLowHealthEnemyInRange(self, point, dist = 3, playerIndex = 0, maxHealth = 10):
        units = self.getUnitsAround(point,dist)
        units = [u for u in units if u.playerIndex != playerIndex and u.health[-1] < maxHealth]
        if units:
            return units[0].pos
        return False
    #-----------------------------------
    def getUnusedUnits(self,player):
        #return list of positions where units haven't been dmgd in a long time
        # -> if they are DFs replace with FFs ?
        return [self.map[pos] for pos in self.allLocations if self.map[pos].avgLossPerTurn(10)<1 and self.map[pos].active and self.map[pos].playerIndex==player]
    #-----------------------------------
    def getCriticalUnits(self,player):
        #return a list of units that will die within the next couple of turns
        return [self.map[pos] for pos in self.allLocations if (self.map[pos].turnsTillDeath()<3 or self.map[pos].health[-1]<10) and self.map[pos].active and self.map[pos].playerIndex==player]
    #-----------------------------------
    def getUnitsOfType(self,type,player):
        # kann nie schaden
        return [self.map[pos] for pos in self.allLocations if self.map[pos].type == type and self.map[pos].playerIndex==player]
    #-----------------------------------
    def getAbsHealthOnMap(self,player):
        #maybe this could be useful?^^ IDK
        ret = 0
        for pos in self.allLocations:
            if not self.map[pos].active or self.map[pos].playerIndex != player:
                continue
            ret += self.map[pos].health
        return ret
    #-----------------------------------
    def getHealthOfUnitsAround(self,pos,dist):
        units = self.getUnitsAround(pos,dist)
        ret = 0
        for unit in units:
            ret += unit.health[-1]
        return ret
    #-----------------------------------
    def getScoreOfUnitsAround(self, pos, dist, playerIndex = -1):
        units = self.getUnitsAround(pos,dist)
        units = [u for u in units if u.playerIndex != playerIndex]
        score = 0
        for unit in units:
            score += unit.value
        #debug_write("{} around {} ({})".format(score,pos, [u.type for u in units if playerIndex != unit.playerIndex]))
        return score
    #-----------------------------------
    def getUnitsScoreHealthOfUnitsAround(self,pos,dist,playerIndex=-1):
        units = self.getUnitsAround(pos,dist)
        units = [u for u in units if u.playerIndex != playerIndex]

        score = 0
        health = 0
        for unit in units:
             
            score += unit.value
            health += unit.health[-1]

        return units,score,health
    #-----------------------------------
    def getUnitsScoreHealthAroundPath(self,path,dist,playerIndex=0):
        units = []
        #damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage
        # could use this aswell?
        for point in path:
            units += self.getUnitsAround(point, dist)

        # units = self.RemoveDuplicates(units) # more acurate if not filtered I think! # TODO
        health = 0
        value = 0
        foundUnits = []
        for unit in units:
            if unit.playerIndex != playerIndex:
                if unit.type == "DF":
                    value += unit.value
                    health += unit.health[-1]
                    foundUnits.append(unit)
                elif unit.type=="EF":
                    value +=unit.value*0.5
                    foundUnits.append(unit)
            else:
                if unit.type=="EF": # and playerIndex == 0:
                    value += unit.value
                    foundUnits.append(unit)
        return foundUnits, value, health
    #-----------------------------------
    def RemoveDuplicates(self,list):
        ret = []
        for element in list:
            if element not in ret:
                ret.append(element)
        return ret
    #-----------------------------------
    def getUnitsAround(self, pos, dist):
        pos = tuple(pos)
        if pos in self.unitsAround:
            return self.unitsAround[pos]
        ret = []
        allPos = [(x,y)
                  for y in range(pos[1]-dist,pos[1]+dist+1)
                  for x in range(pos[0]-dist,pos[0]+dist+1) 
                  if self.distanceBetween((x,y),pos) < dist + 0.51]

        # really this is what makes this function so slow!
        allLocations = self.allLocations
        filteredPos = [p for p in allPos if p in allLocations and p != pos ] # slow?

        for pos in filteredPos:
            if self.map[pos].active:
                ret.append(self.map[pos])

        self.unitsAround[pos] = ret

        return ret # all active units in range.
    #-----------------------------------
    def distanceBetween(self, location_1, location_2):
        x1, y1 = location_1
        x2, y2 = location_2
        return sqrt((x1 - x2)**2 + (y1 - y2)**2)
    #-----------------------------------
    def setPriority(self,pos,priority):
        pos = tuple(pos)
        if not pos in self.allLocations:
            return
        self.map[pos].priority = priority
    #-----------------------------------
    def resetPritority(self):
        for pos in self.allLocations:
            self.map[pos].priority = 0
    #-----------------------------------
    def getHighestPriorities(self):
        ret = []
        for pos in self.allLocations:
            ret.append([self.map[pos].pos, self.map[pos].priority])
        ret.sort(key = lambda x:x[1])
        return reversed([r[0] for r in ret]) #positions only, highestPriority first
    #-----------------------------------
    def hasUnit(self,pos):
        return self.map[tuple(pos)].active
    #-----------------------------------
    def get_all_locations(self):
        ARENA_SIZE = 28
        all_locations = []
        for i in range(ARENA_SIZE):
            for j in range(ARENA_SIZE):
                if (self.in_arena_bounds([i, j])):
                    all_locations.append([i, j])
        return all_locations
    #-----------------------------------
    def in_arena_bounds(self, location):
        x, y = location
        ARENA_SIZE = 28
        HALF_ARENA = ARENA_SIZE / 2

        row_size = y + 1
        startx = HALF_ARENA - row_size
        endx = startx + (2 * row_size) - 1
        top_half_check = (y < HALF_ARENA and x >= startx and x <= endx)

        row_size = (ARENA_SIZE - 1 - y) + 1
        startx = HALF_ARENA - row_size
        endx = startx + (2 * row_size) - 1
        bottom_half_check = (y >= HALF_ARENA and x >= startx and x <= endx)

        return bottom_half_check or top_half_check
    #-----------------------------------
    def get_edge_locations(self, quadrant_description):
        return self.get_edges()[quadrant_description]
    #-----------------------------------
    def get_edges(self):
        """Gets all of the edges and their edge locations

        Returns:
            A list with four lists inside of it of locations corresponding to the four edges.
            [0] = top_right, [1] = top_left, [2] = bottom_left, [3] = bottom_right.
        """

        ARENA_SIZE = 28
        HALF_ARENA = ARENA_SIZE // 2

        top_right = []
        for num in range(0, HALF_ARENA):
            x = HALF_ARENA + num
            y = ARENA_SIZE - 1 - num
            top_right.append([int(x), int(y)])
        top_left = []
        for num in range(0, HALF_ARENA):
            x = HALF_ARENA - 1 - num
            y = ARENA_SIZE - 1 - num
            top_left.append([int(x), int(y)])
        bottom_left = []
        for num in range(0, HALF_ARENA):
            x = HALF_ARENA - 1 - num
            y = num
            bottom_left.append([int(x), int(y)])
        bottom_right = []
        for num in range(0, HALF_ARENA):
            x = HALF_ARENA + num
            y = num
            bottom_right.append([int(x), int(y)])
        return [top_right, top_left, bottom_left, bottom_right]
    #-----------------------------------

       