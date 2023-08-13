from em_util import removeDuplicates
from em_util import predictedTurnsTillDeath
from gamelib import debug_write, GameState
from typing import Optional
"""
class to store and maintain player-specific data
"""

class Player:
    def __init__(self,playerIndex=0, game_state: Optional[GameState] = None):
        # pylint: invalid-name
        self.spawnHistory = []
        self.spawnPoints = []
        self.health = []
        self.index = playerIndex
        self.Update(game_state = game_state)
        self.healthSinkRate = 0
        self.startEdges = []
        self.targetEdges = []
        self.scores = []
        self.bestScore = None
        self.critical = []
        self.extraCritical = []
        if game_state is not None:
            if self.index==0: # player
                self.startEdges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
                self.targetEdges = game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)
            else: # enemy
                self.startEdges = game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)
                self.targetEdges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
    #----------------------------------------------------------------
    # returns all spawnpoints, but with previously used spawnpoints sorted first for enemy, to make sure to test the critical paths
    def GetSpawnPoints(self):
        if self.index==1:
            ret = self.spawnPoints + self.startEdges
            ret = removeDuplicates(ret)
            return ret
        return self.startEdges

    #----------------------------------------------------------------
    def Update(self, units = [], game_state=None,scores = []):
        self.game_state = game_state

        self.bits = game_state.get_resource(game_state.BITS, self.index)
        self.cores = game_state.get_resource(game_state.CORES, self.index)

        self.spawnHistory.append(units)
        self.spawnPoints+=[u.pos for u in units if not u.stationary]


        self.health.append(game_state.my_health if self.index==0 else game_state.enemy_health)
        self.turnsTillDeath = predictedTurnsTillDeath(self.health,10) # VALUE: adjust lookback

        self.scores = scores

        # TODO: rethink using extracrit at all...!
        if self.scores:
            self.bestScore = self.GetBestScore(False) #self.index==1)
            #debug_write("SCORE: best score for player {}: {} ({})".format(self.index, self.bestScore.startPoint,self.bestScore.value))
        else: # didn't find any scores!
            pass
            # TODO: should probably do something to clear the path!


        self.nextPI = self.PredictNextSpawn(game_state.PING)
        self.nextSI = self.PredictNextSpawn(game_state.SCRAMBLER)
        self.nextEI = self.PredictNextSpawn(game_state.EMP)
    #----------------------------------------------------------------
    def GetBestScore(self,useExtraCrit = False):# true for ENEMY


        self.critical = [score for score in self.scores if score.pathToEnd]
        self.extraCritical = [score for score in self.critical if score.startPoint in self.spawnPoints[:15]] # VALUE

        maxValueAtSpawn = 0.1 # no more than 1 enemy destructor near spawnPoint!

        if useExtraCrit:
            if self.extraCritical:
                debug_write("found extraCrit at {}".format(self.extraCritical[0].startPoint))
                return self.extraCritical[0]


        for e in self.critical:
            if e.valueNearSpawn<=maxValueAtSpawn:
                #debug_write("first try: {}".format(e.valueNearSpawn))
                return e
        #debug_write("didnt find good critical score!")

        # if we can't hit the opposing side return the best score
        for e in self.scores:
            if e.valueNearSpawn<maxValueAtSpawn:
                #debug_write("second try: {}".format(e.valueNearSpawn))
                return e

        return None # no scores found!?

    # those funcs could be used to test if a strategy is valid or if it'd take to long to deploy...
    #----------------------------------------------------------------
    def TurnsTillBits(self,futureBits):
        if futureBits < self.bits:
            return 0
        turn = 1
        while self.game_state.project_future_bits(turn, self.index) < futureBits:
            turn+=1
        return turn
    #----------------------------------------------------------------
    def TurnsTillCores(self,futureCores):
        if futureCores < self.cores:
            return 0
        turn = 1
        while self.game_state.project_future_cores(turn, self.index) < futureCores:
            turn+=1
        return turn
    #----------------------------------------------------------------
    def BitsInTurns(self,turns):
        return self.game_state.project_future_bits(turns, self.index)
    #----------------------------------------------------------------
    def CoresInTurnes(self,turns):
        self.game_state.project_future_cores(turns,self.index)
    #----------------------------------------------------------------
    def GetPossibleSpawnPoints(self):
        return [item for item in self.startEdges if not self.game_state.contains_stationary_unit(item)]
    #---------------------------------------------------------------------
    def CanAfford(self,type, amount):
        if self.game_state.number_affordable(type, self.index)>=amount:
            return True
        return False
    #---------------------------------------------------------------------
    def AmountAffordable(self,type):
        return self.game_state.number_affordable(type, self.index)
    #---------------------------------------------------------------------
    def GetCost(self,type,amount):
        cost = 0
        for _ in range(amount):
            cost += self.game_state.type_cost(type)
    #---------------------------------------------------------------------
    def ThreatLevel(self, futureTurns = 0, attackCost = False, score = None ): # TODO: implement futureTurns

        # returns the score.value / attackCost ratio!
        # if this ratio is smaller than 1 -> likely to score
        # if it's smaller than 0 -> dayum, this is gonna sting!
        if not score:
            currentScore = self.bestScore
        else:
            currentScore = score
        unitType, turns = self.PredictedSpawn()

        # use attackCost if i want to know how effective attacking with this amount of bits would be
        # TODO: # BUG: negative scores aren't calculated right here...!
        # not that it would matter too much, negative score is negative score...
        if not currentScore:
            return 99
        if attackCost:
            return currentScore.value / int(attackCost)

        ratio = 1
        if unitType:
            cost = self.BitsInTurns(turns)

            ratio = currentScore.value / int(cost)
           

            if turns > 0: # not predicted to spawn this turn
                # player less likely to spawn units, but could always be pingrushing or sth?
                # he could still surprise me by spwning something else right now?
                # maybe use the old function to get the worst-case szenario! # TODO:
                cost = self.BitsInTurns(0)
                ratio = currentScore.value / int(cost)

        return ratio
    #---------------------------------------------------------------------
    def AttacksCorner(self):
        return self.bestScore.lengthInEnemyTerritory < 6 and self.bestScore.pathToEnd
    #---------------------------------------------------------------------
    def HasMaze(self):
        return (self.bestScore.pathLength - self.bestScore.lengthInEnemyTerritory) > 27 # VALUE
    #---------------------------------------------------------------------
    def CanSpawnCannon(self, gameGrid, enemy, maxDefense = 2):
        leftPossible=False
        rightPossible=False
        if self.index == 0:
            leftPossible  = True if gameGrid.hasUnit([1,14])  or gameGrid.hasUnit([2,14])  else False
            rightPossible = True if gameGrid.hasUnit([26,14]) or gameGrid.hasUnit([25,14]) else False
        else:
            leftPossible  = True if gameGrid.hasUnit([1,13])  or gameGrid.hasUnit([2,13])  else False
            rightPossible = True if gameGrid.hasUnit([26,13]) or gameGrid.hasUnit([25,13]) else False

        # dont do cannon if there's to much defense
        if self.DefenseAroundCorner(gameGrid,"left") > maxDefense:
            leftPossible = False
        if self.DefenseAroundCorner(gameGrid,"right") > maxDefense:
            rightPossible = False

        # pick opposite edge of enemy spawn, just in case he'll spawn EMPS and ruin the cannon
        if leftPossible and enemy.bestScore.startPoint[0]>13:
            return "left"
        if rightPossible and enemy.bestScore.startPoint[0]<14:
            return "right"

        # if that's not possible: time the cannon!
        if leftPossible and enemy.PredictNextSpawn(self.game_state.EMP) !=0:
            return "left"
        if rightPossible and enemy.PredictNextSpawn(self.game_state.EMP) !=0:
            return "right"
        return False
    #---------------------------------------------------------------------
    def PredictNextSpawn(self,type):
        # parse through history, and check how many units the enemy usually spawns
        # figure out if he's likely to spawn one now.
        numSpawns = 0
        numUnits = 0
        avgUnits = 0
        # only use recent spawn history...!
        for turn in self.spawnHistory[-10:]: # VALUE
            unitSpawned = False
            for unit in turn:
                if unit: # does this make sense?
                    if unit.unit_type == type:
                        numUnits+=1
                        unitSpawned = True
            if unitSpawned:
                numSpawns+=1

        if numSpawns>0:
            avgUnits = numUnits/numSpawns
        else: # didn't recently spawn unit type
            return -1

        # return number of turns till he has enough bits to spawn his avgAmount
        cost = avgUnits * self.game_state.type_cost(type)
        return self.TurnsTillBits(cost)

    #---------------------------------------------------------------------
    def DefenseAroundCorner(self, gameGrid, side):
        leftPoint  = [ 1,13] if self.index==0 else [ 1,14]
        rightPoint = [26,13] if self.index==0 else [26,14]

        radius = 2
        if side=="left":
            return gameGrid.getScoreOfUnitsAround(leftPoint,radius,self.index) #self, pos, dist, playerIndex = -1):
        else:
            return gameGrid.getScoreOfUnitsAround(rightPoint,radius,self.index)

    #---------------------------------------------------------------------
    def PredictedSpawn(self):
        # [None,None] if not spawned recently, else type + turns till spawn
        spawns = []
        spawns.append([self.game_state.PING,self.PredictNextSpawn(self.game_state.PING)])
        spawns.append([self.game_state.EMP,self.PredictNextSpawn(self.game_state.EMP)])
        spawns.append([self.game_state.SCRAMBLER,self.PredictNextSpawn(self.game_state.SCRAMBLER)])
        spawns.sort(key = lambda x: x[1], reverse = False)
        spawns = [s for s in spawns if s[1]>=0 ] # only return valid predictions
        if spawns:
            return spawns[0]
        return [None, None]
    #---------------------------------------------------------------------
    def GetSplitPathLengths(self,score):
        pathLength0 = 0
        pathLength1 = 0
        if not score:
            return 0, 0
        for point in score.path:
            if self.index == 0:
                if point[1]<14:
                    pathLength0 += 1
                else:
                    pathLength1 += 1
            else:
                if point[1]<14:
                    pathLength1 += 1
                else:
                    pathLength0 += 1
        return pathLength0, pathLength1
    #---------------------------------------------------------------------
