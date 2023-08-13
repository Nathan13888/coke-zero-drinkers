from em_score import Score

import gamelib

import em_util
import copy
from em_timer import Timer
import time
from em_pathFinding2 import PathFinder
import em_log as log




# TODO: remove points (as in: optimize!)
class Scoring:
    def __init__(self,game_state):
        self.scores = []
        self.player = None
        self.gameGrid = None
        self.game_state = game_state
        self.optimized = False
        self.timer = Timer()
        self.pathFinder = PathFinder(game_state)
        #log.ACTIVE = False # disable all console output

        #Print("SCORING: INIT DONE.")
    def GetScores(self, player, gameGrid, game_state, optimized = False, threading = True):

        self.player = player
        self.gameGrid = gameGrid
        self.game_state = game_state
        self.optimized = optimized
        self.timer.reset()

        scores = [] # ret val





        if threading:

            import multiprocessing as mp # for multithreading
            #----------------------------------
            # the MultiProcessing block -> can be moved to new func !

            args = [[point,
                     player,
                     gameGrid,
                     game_state,
                     optimized]
                    for point in player.GetSpawnPoints()]

            inQ = mp.Manager().Queue()
            outQ = mp.Manager().Queue()

            n_workers =  mp.cpu_count()

            workers = [mp.Process(target=ThreadWorker, args=(self,inQ,outQ,i))
                       for i in range(n_workers)]

            # start the workers
            for w in workers:
                w.start()

            #put in some work
            for arg in args:
                inQ.put(arg)
            # tell all workers, no more data (one msg for each)
            for _ in range(n_workers):
                inQ.put(None)

            # get all scores that have been found:
            while True:
                running = any(w.is_alive() for w in workers)
                while not outQ.empty():
                    scores.append(outQ.get())
                if not running:
                    break

            #----------------------------------

        else: # no threading
            GetScore = self.GetScore # ?
            scores = [GetScore(point, player, gameGrid, game_state, optimized = optimized) for point in player.GetSpawnPoints()]

        scores = [s for s in scores if s]


        # filter paths that end in my own half!

        if player.index==0:
            scores = [score for score in scores if score.endPoint[1]>12]
        else:
            scores = [score for score in scores if score.endPoint[1]<14]

        scores.sort(key = lambda x: (x.value,x.health,x.lengthInEnemyTerritory), reverse = False) # sort by Score -> lowest first


        #log.print("found {} scores in {:.4f} seconds".format(len(scores), self.timer.timePassed()))
        return scores

    #------------------------------------------------------------------
    def GetPath(self, startPoint, game_state, targetEdge = None):
        #log.print("getting path for {}".format(startPoint))
        getPath = self.pathFinder.GetPath
        if not targetEdge:
            return getPath(game_state,startPoint)
        
        return getPath(game_state,startPoint, targetEdge) # game_state,start,target = None

    #------------------------------------------------------------------
    def GetScore(self, startPoint, player, gameGrid, game_state, targetEdge = None, path = None, optimized = False, width = 3):
        if not path:
            path = self.GetPath(startPoint, game_state, targetEdge)

        if not path:
            #log.print("ERR: no path found")
            return None

        if optimized:
            path = self.OptimizePath(path, player, gameGrid, game_state, targetEdge)


        thisLen=0
        if player.index==0:
            thisLen = len([p for p in path if p[1]>12]) # len in enemyTerritory
        else:
            thisLen = len([p for p in path if p[1]<13])


        thisUnits, thisScore, thisHealth = gameGrid.getUnitsScoreHealthAroundPath(path, width, player.index)
        unitsNearSpawn, valueNearSpawn, healthNearSpawn = gameGrid.getUnitsScoreHealthOfUnitsAround(path[0], width, player.index)
        unitsNearBreach, valueNearBreach, healthNearBreach = gameGrid.getUnitsScoreHealthOfUnitsAround(path[-1], width, player.index)


        return Score(
            path = path,
            value = thisScore, #number of spaces i will be exposed to destructors
            health = thisHealth,
            units = thisUnits,
            pathToEnd = path[-1] in player.targetEdges,
            lengthInEnemyTerritory = thisLen,
            valueNearSpawn = valueNearSpawn,
            valueNearBreach = valueNearBreach,
            unitsNearSpawn = unitsNearSpawn,
            unitsNearBreach = unitsNearBreach,
            healthNearSpawn = healthNearSpawn,
            healthNearBreach = healthNearBreach
            )

    #------------------------------------------------------------------
    def OptimizePath(self, path, player, gameGrid, _game_state, targetEdge = None):
        #Print("OPTIMIZER working")

        # TODO:
        # this whole thing won't work now, because i'd have to update the stationary units in my pathing class for it to return anything different..!!!

        game_state = copy.deepcopy(_game_state) # slow


        target = em_util.getTargetEdge
        removeUnit = game_state.game_map.remove_unit
        HasLowHealthEnemyInRange = self.HasLowHealthEnemyInRange
        GetPath = self.pathFinder.GetPath
        playerIndex = player.index
        startPoint = path[0]
       
        currentStep = 0
        if not targetEdge:
            targetEdge = em_util.getTargetEdge(path[0],game_state)

        optimizing = True
        while(optimizing):
            for point in path:
                lowHealthUnit = HasLowHealthEnemyInRange(game_state.game_map,gameGrid, point, playerIndex, maxHealth = 17) # TODO: find correct value!
                if lowHealthUnit:
                    log.print("OPTIMIZER updating Path!")
                    removeUnit(lowHealthUnit)
                    # TODO: change to pathfinder class!
                    #path = path[:currentStep] + findPath(point, target(startPoint,game_state))

                    path = path[:currentStep] + GetPath(game_state, point, target = target(startPoint, game_state)) # game_state,start,target = None

                currentStep += 1
            optimizing = False
        return path

    #------------------------------------------------------------------
    def HasLowHealthEnemyInRange(self,game_map, gameGrid ,pos, playerIndex = 0,maxHealth = 10):
        pos = tuple(pos)
        neighbors = gameGrid[pos].neighbors
        for neighbor in neighbors:
            if game_map[neighbor]: # will fail ?
                if game_map[neighbor][0].player_index != playerIndex:
                    if game_map[neighbor][0].stationary:
                        if game_map[neighbor][0].stability < maxHealth:
                            return neighbor
        return False

    #------------------------------------------------------------------
    def SimulateTurn(self,game_map,gameGrid,startingPoint,units):
        pass # todo: ... turn simulation^^
#------------------------------------------------------------------
def ThreadWorker(scoringClass, inQ, outQ, id):
    timer = Timer()
    ret = None
    counter = 0

    while True:
        data = inQ.get()
        # this is the 'TERM' signal
        if data is None:
            #Print("THREADING ----------> ended after {} jobs in {:.4f}!".format(counter,timer.timePassed()))
            break
        if timer.timePassed()>2.3:
            log.print("----------> Timed out!")
            break

        """
        args = [[point,
                 player,
                 gameGrid,
                 game_state,
                 optimized]
        """
        #def GetScore(self, startPoint, player, gameGrid, game_state, targetEdge = None, path = None, optimized = False, width = 3):

        ret = scoringClass.GetScore(data[0],
                                    data[1],
                                    data[2],
                                    data[3],
                                    targetEdge = None,
                                    optimized = data[4])
        #put result to out queue
        outQ.put(ret)
        counter += 1




#------------------------------------------------------------------
