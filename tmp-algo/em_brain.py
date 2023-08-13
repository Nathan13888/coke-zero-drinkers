from gamelib import debug_write, GameState
from em_player import Player
from em_timer import Timer
from em_gameGrid import GameGrid
from em_score import Score
from em_util import BuildQueue
import em_util
import em_log as debug
from em_strategy import Strategy
import em_buildingPlans as BuildingPlans
from em_scoring import Scoring
from copy import deepcopy
import queue
from typing import Optional, cast

"""-------------------------------------------------------------

# TODO:

- rethink scoring: how to use health? lower the score of low-health units?
- also: for health-scores: don't consider filters!
- also: when spawning EMPs: search for pathes that will do high damage, but w/ low score! (-> few destructors)


-------------------------------------------------------------"""

#------------------------------------------------------------------
# THE BRAIN CLASS!!
#------------------------------------------------------------------

class Brain:
    def __init__(self):
        debug.ACTIVE = True
        self.timer = Timer()
        self.log = []


        self.history = []
        self.hits = []  #set from on_action
        self.damage = [] #set from on_action
        self.game_state: Optional[GameState] = None  #set from update
        self.enemyUnits = [] #set from on_action
        self.playerUnits = [] #set from on_action

        self.enemyHealth = 0
        self.playerHealth= 0
        self.playerScores = []
        self.enemyScores = []

        # is anything here still in use?? - don't think so.
        self.enemySpawnPoints = []
        self.enemyHitPoints = []
        self.enemyPaths = [] # unused
        self.playerPaths = [] # unused
        self.spawn = [] # unused

        self.enemyEdgePoints = [] # set on setup
        self.playerEdgePoints = []# set on setup

        self.enemyScored = False  # unused
        self.playerScored = False # unused

        self.buildQueue = BuildQueue()


        self.tasks = queue.Queue()
    #------------------------------------------------------------------
    def start(self,game_state):
        self.game_state = game_state
        self.playerEdgePoints = em_util.getEdgePoints(game_state,0)
        self.enemyEdgePoints = em_util.getEdgePoints(game_state,1)
        self.allLocations = em_util.getAllLocations(game_state)

        self.gameGrid = GameGrid(game_state.game_map)

        self.player = Player(playerIndex=0, game_state = game_state)
        self.enemy  = Player(playerIndex=1, game_state = game_state)
        self.playerHealth = game_state.my_health
        self.enemyHealth = game_state.enemy_health
        self.scoring = Scoring(game_state)
        self.strategy = Strategy(game_state,self.player,self.enemy,self)

        debug.print("-------------------------------")
        debug.print(" init done - ready for action! ")
        debug.print("-------------------------------")
    #------------------------------------------------------------------
    def update(self,game_state):
        debug.print(".   ------------------------------------------------------------------------------------------")
        debug.print(".              ========== turn {}  ========== ".format(game_state.turn_number))
        debug.print(".   ------------------------------------------------------------------------------------------")
        game_state.suppress_warnings(True) # do I need to re-set this every turn?
        self.timer.reset()
        self.game_state = game_state

        # analyze what happend last turn:
        self.analyzeActionPhase()

        #if self.GridChanged(): # this could speed things up by quite a bit!
        self.playerScores = self.scoring.GetScores(self.player, self.gameGrid,self.game_state, optimized = True, threading = False)
        self.enemyScores  = self.scoring.GetScores(self.enemy, self.gameGrid,self.game_state, optimized = False, threading = False)
        
        debug.print("Getting all scores took {:.2f} seconds".format(self.timer.timePassed()))
        #debug.print_values_dict(self.gameGrid.getUnitMap(),self.game_state.game_map,scaling=False )

        # update players
        self.player.Update(self.playerUnits[-1] if self.playerUnits else [],
                           self.game_state,
                           self.playerScores)

        self.enemy.Update(self.enemyUnits[-1] if self.enemyUnits else [],
                          self.game_state,
                          self.enemyScores)

    
        # all info is gathered, build strategy!
        self.createStrategy()

        # i can use timer.timeLeft() to check if I have time to do some more work...!
        if self.timer.timeLeft()>2: # seconds
            pass
             # TODO: can i prepare something for next turn?

        debug.print("--------------------")
        debug.print("player: {} / enemy: {}".format(self.player.health[-1],self.enemy.health[-1]))
        debug.print("processing turn {} took {:.2f} secs".format(game_state.turn_number,self.timer.timePassed()))

    #------------------------------------------------------------------
    def createStrategy(self):

        # update strategy base values
        self.strategy.reset(self.game_state,
                            self.player,
                            self.enemy,
                            self.gameGrid)
        # look at bestScore, and the best health score, and see if there's a point in sending pings!
        healthScores = self.GetScoresByHealth(self.player.index)
        
        # threatlevels (ratio of score/bits)
        playerThreatLevel = self.player.ThreatLevel(10) 
        enemyThreatLevel = self.enemy.ThreatLevel()


        # debug print for balancing:
        debug.print("PLAYER: Cores: {} Bits: {}".format(self.player.cores, self.player.bits))
        debug.print("ENEMY : Cores: {} Bits: {}".format(self.enemy.cores, self.enemy.bits))
        #debug.print("SCORE: {:.2f} / HEALTH: {}".format(self.player.bestScore.value, healthScores[0].health))
        #debug.print("Value Near Spawn: {}".format(self.player.bestScore.valueNearSpawn))
        if self.player.bestScore and self.enemy.bestScore:
            debug.print("THREAT: player: {:.2f} (score: {:.2f} / {} - {})".format(playerThreatLevel,self.player.bestScore.value, self.player.bestScore.health, self.player.bestScore.startPoint))
            debug.print("THREAT: enemy:  {:.2f} (score: {:.2f} / {} - {})".format(enemyThreatLevel,self.enemy.bestScore.value, self.enemy.bestScore.health,self.enemy.bestScore.startPoint))
        
        #for score in self.enemy.scores:
        #    self.print("{} -> {}, {} // {}".format(score.startPoint,score.endPoint, score.value,len(score.units)))
            #for u in score.units:
            #    self.print("{}: {} {}".format(u.playerIndex, u.pos, u.type))

            debug.print("pathToEnd: {}".format(self.player.bestScore.pathToEnd))
            debug.print(" {} / {}".format(len(self.player.scores), len(healthScores)))


        # """
        # now i know:
        # - the worst attack my enemy could do
        # - how many units he could spawn
        # - which type is most likely to spawn
        # """

        # how to figure out if its better to build defense or to wait?

    


        # create strategy for this turn:
        currentStrategy = "adaptive"
        side = None

        game_state = cast(GameState, self.game_state)

        # first turns
        if game_state.turn_number<2:
            currentStrategy = "maze"
            self.strategy.AddUnits(game_state.SCOUT, 10, self.player.bestScore.startPoint)
        elif self.player.bestScore == None:
            # no scores found!? - use cannon to clear a way!
            side = self.player.CanSpawnCannon(self.gameGrid,self.enemy) # "left"/"right"/False
            if side:
               
                currentStrategy = "pingCannon"
                self.strategy.AddUnits(game_state.SCOUT,19,BuildingPlans.GetPingCannonSpawn(side)) 
            else:
                pass
                #self.strategy.AddUnits(game_state.EMP,5,self.player.bestScore.startPoint)
        # if self destructing
        elif not self.player.bestScore.pathToEnd:
            # check if i should build a cannon
            # i'm kinda safe here, so dont worry if it takes a couple of turns
            side = self.player.CanSpawnCannon(self.gameGrid,self.enemy) # "left"/"right"/False
            if side and not self.enemy.AttacksCorner():
                currentStrategy = "pingCannon"
                self.strategy.AddUnits(game_state.SCOUT,19,BuildingPlans.GetPingCannonSpawn(side)) 
            else:
                # find path with least opposition near the end - is this smart? idk^^
                #self.player.scores.sort(key = lambda x: x.valueNearBreach) # does this work?
                self.strategy.AddUnits(game_state.EMP,5,self.player.bestScore.startPoint)
                # maybe do EMPs here instead? hmm....... 
                # how would I decide if emps are better than pings? -> health around endpoint -> TODO
        

        elif self.player.CanSpawnCannon(self.gameGrid, self.enemy, maxDefense = 0) and self.player.cores > 10: # "free ping cannon" - this /could/ be good? # TODO
            self.print("# discount pingcannon...")
            side = self.player.CanSpawnCannon(self.gameGrid,self.enemy) # "left"/"right"/False
            currentStrategy = "pingCannon"
            self.strategy.AddUnits(game_state.SCOUT,19,BuildingPlans.GetPingCannonSpawn(side)) 


        elif playerThreatLevel < 0.8 or healthScores[0].health < 100: # VALUE # should score w/ default attack:
            self.strategy.AddUnits(game_state.SCOUT,10,self.player.bestScore.startPoint)
        elif playerThreatLevel < 1.1 or healthScores[0].health < 500: # TODO test this
            self.strategy.AddUnits(game_state.EMP,3,self.player.bestScore.startPoint)
       
        else: # playerThreatLevel >= 1
            if self.player.ThreatLevel(attackCost = 15) < 0.8: # bigger attack might score
                self.strategy.AddUnits(game_state.SCOUT,15,self.player.bestScore.startPoint)
            elif self.player.ThreatLevel(attackCost = 19) < 0.8: # bigger attack might score
                self.strategy.AddUnits(game_state.SCOUT,19,self.player.bestScore.startPoint)
            else:
                side = self.player.CanSpawnCannon(self.gameGrid,self.enemy)
                if side:
                    currentStrategy = "pingCannon"
                    self.strategy.AddUnits(game_state.SCOUT,19,BuildingPlans.GetPingCannonSpawn(side))
                else:
                    # well fuck^^
                    # impenetrable defense and not able to build a cannon... what to do now?
                    currentStrategy = "maze"
                    self.strategy.AddUnits(game_state.EMP,5,BuildingPlans.GetMazeSpawn()) #"bruteforce" xD
                    # are there other times when a maze would be a good idea?
                    # - if the enemy is pingrushing and i have lot's of cores
                    # - ???




        self.strategy.SetCurrentStrategy(currentStrategy, side, enemyThreatLevel,playerThreatLevel)

        
        



        self.strategy.CreateOffense()
        self.strategy.CreateDefense()

        # sheduled reconstruction:
        self.buildQueue.process(self.game_state,self.strategy.notBuildAllowed)

        #deploy units
        self.strategy.DeployDefense()
        self.strategy.DeployOffense()



        # TODO: OOOhhh I could use the unusedUnits to figure out if i can replace some destructors with filters!
     
        # add critical units to queue to be replaced!
        # TODO: think about when this is a good strategy..!
        # maybe only do this for units that are in/near my enemys best path?
        locsToRebuild, unitsToRebuild = self.GetCriticalUnits(encryptors=False)


        if unitsToRebuild:
            game_state.attempt_remove(locsToRebuild)
            self.buildQueue.push(unitsToRebuild)

    #------------------------------------------------------------------
    def GetCriticalUnits(self,playerIndex = 0, encryptors = True):
        unitsToRebuild = self.gameGrid.getCriticalUnits(playerIndex)
        if not encryptors:
            unitsToRebuild = [unit for unit in unitsToRebuild if unit.type is not game_state.ENCRYPTOR]

        locs = [unit.pos for unit in unitsToRebuild]
        units = [[unit.type, unit.pos] for unit in unitsToRebuild]

        return locs, units
    #------------------------------------------------------------------
    def RemoveUnusedUnits(self):
        # Remove unused units -> figure out WHEN this is apropriate...!
        unused = self.gameGrid.getUnusedUnits(self.player.index)
        locs = [p.pos for p in unused if p.type != game_state.ENCRYPTOR]
        if locs:
            game_state.attempt_remove(locs)

    #------------------------------------------------------------------
    def analyzeActionPhase(self):
        # update history
        # TODO: Weird logic with game_state and self.game_state which should be equivalent
        game_state = cast(GameState, self.game_state)
        map = game_state.game_map
        allUnits = map.get_all_units

        currentUnits = [u for u in allUnits() if u.stationary]
        self.history.append([u for u in currentUnits if not u.pending_removal]) # could be used to predict if a unit well be rebuilt (and their order of rebuilding etc...)!

        # update the map:
        # replace destroyed enemy units
        self.game_state = em_util.replaceDeletedEnemyUnits(game_state,self.history)

        # do not consider enemy units that are marked for deletion
        unitsToRemove = [u for u in currentUnits if u.pending_removal]
        for unit in unitsToRemove:
            self.print("removing unit {} bc marked for deletion".format(unit.pos))
            map.remove_unit(unit.pos)

        # process previous ActionState:
        # check if someone scored -> to be used laters
        self.enemyScored = False
        self.playerScored = False

        if game_state.my_health <self.playerHealth:
            self.enemyScored = True
            self.print("SCORE: enemy scored ({})".format(self.playerHealth-game_state.my_health))
        if game_state.enemy_health < self.enemyHealth:
            self.playerScored = True
            self.print("SCORE: player scored ({})".format(self.enemyHealth-game_state.enemy_health))
        self.enemyHealth = game_state.enemy_health
        self.playerHealth = game_state.my_health

        # update gameGrid
        self.gameGrid.update(game_state.game_map)
        self.print("... analysis of previous turn done, everything up2date!")
        return
    #------------------------------------------------------------------
    def GridChanged(self):
        if(len(self.history)>1):

            pos1 = [tuple(unit.pos) for unit in self.history[-1] if unit.stationary]
            pos2 = [tuple(unit.pos) for unit in self.history[-2] if unit.stationary]
            # return true if element is only in one of those lists
            self.print("CHANGE: {}".format(len(set(pos1).symmetric_difference(pos2)) > 0))
            # could use any() here, right? : )
            return len(set(pos1).symmetric_difference(pos2)) > 0
        return True


            #changed =  [x for x in self.history[-1] if x not in self.history[-2]] # those are only units added, not units removed...
            #changed += [x for x in self.history[-2] if x not in self.history[-1]]
            #return len(changed)>0

        #return True #
    #------------------------------------------------------------------
    def GetScoresByHealth(self, playerIndex):
        healthScores = deepcopy(self.player.scores) # "SLOW", also ... needed?
        healthScores.sort(key = lambda x: x.health, reverse = False) # sort by Health -> lowest first
        return healthScores
    #------------------------------------------------------------------
    def print(self,msg):
        debug.print(msg)
    #------------------------------------------------------------------
    def dumpLog(self):
        debug.dumpLog()
    #------------------------------------------------------------------
