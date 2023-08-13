from em_util import BuildQueue
import em_util # used?
import em_buildingPlans as BuildingPlans
from typing import Literal

import gamelib
#------------------------------------------------------------------
class Strategy:
    def __init__(self,game_state,player,enemy,brain):
        self.minCores = 6
        self.maxCores = 99
        self.reversed = False
        # self.side = False
        self.side: Literal["left", "right"] = "left"
        self.units = []
        self.notBuildAllowed = []
        self.defenseUnits = []
        self.offenseUnits = []
        self.encryptors = []
        self.player = player
        self.enemy = enemy
        self.cleared = True
        self.missing = 0
        self.defenseBuilt = False
        self.game_state = game_state
        self.spawnPoint = []
        self.currentCannonSide = "left"
        self.name = "default"
        self.brain = brain
        self.enemyThreatLevel = 0
        self.playerThreatLevel = 0
        self.offenseActive = False
        self.offenseCost = 0
        self.spawnEncryptors = True
        self.numOffenseTurns = 0

        self.maxEncryptorsPerTurn = 3

        # not build-allowed -> tuples!?

        self.allowedToChange = True



    def print(self,msg):
        self.brain.print("strt: {}".format(msg))
    #------------------------------------------------------------------
    def reset(self,game_state,player,enemy,gameGrid):
        self.game_state = game_state
        self.defenseUnits = []
        self.player = player # shouldnt have to set these each turn?
        self.enemy = enemy
        self.gameGrid = gameGrid
        if self.player.bestScore:
            self.spawnPoint = self.player.bestScore.startPoint
        if not self.offenseActive:
            self.offenseCost = 0
            self.defenseUnits = []
        # TODO does this work as expected?
        if self.name=="pingCannon":
            pass
           
    #------------------------------------------------------------------
    def AddUnits(self,type,amount,spawnPoint):
        
        if not self.offenseActive:
            self.print("adding {} {} to offense".format(amount, type))

            for _ in range(amount):
                self.offenseUnits.append([type,spawnPoint])
                self.offenseCost += self.game_state.type_cost(type)

            self.print("new offense costs {} bits".format(self.offenseCost))
            self.offenseActive = True
            self.numOffenseTurns = self.player.TurnsTillBits(self.offenseCost) # overall duration of this offense

    #------------------------------------------------------------------
    def CreateDefense(self):
        if self.name=="default":
            self.AddaptiveDefense()
        elif self.name == "pingCannon":
            self.PingCannonDefense()
        elif self.name == "maze":
            self.MazeDefense()
        else:
            self.AddaptiveDefense()

    #------------------------------------------------------------------
    def AddaptiveDefense(self):
        bottleNecks = False # ??
        
        #offensePath = self.player.bestScore.path
        #self.notBuildAllowed = [p for p in offensePath if p[0]>5 and p[0]<22]   # fill corners

        units, notBuildAllowed =  BuildingPlans.GetAdaptiveDefense(
                                                         self.game_state,
                                                         self.gameGrid,
                                                         self.player,
                                                         self.enemy,
                                                         reversed = self.reversed,
                                                         useBottleNecks = bottleNecks)




        self.defenseUnits += units
        self.notBuildAllowed += notBuildAllowed # "could work" # TODO:

        if self.enemyThreatLevel > 1:
            self.defenseUnits = [] # don't bother

    #------------------------------------------------------------------
    def PingCannonDefense(self):
        self.print("MOTHERFUCKIN PING CANNON")
        self.spawnEncryptors = False #don't build encryptors this turn, gotta build a cannon! ... building my own encs
        self.defenseUnits = BuildingPlans.GetPingCannon(self.game_state,self.side)

        # only delete if you can replace the stuff right away!
        #self.print("cannon on {} side".format(self.side))

        #defenseCost = BuildingPlans.GetMinCoresForPingCannon()
        defenseCost = BuildingPlans.CheckIfBuilt(self.game_state, "pingCannon",self.side)
        #TODO take into account cores from refund (from deleted units)
        defenseCost -= BuildingPlans.GetRefundAmount(self.game_state,BuildingPlans.GetNotBuildAllowedByCannon(self.side))

        turnsTillOffense = self.player.TurnsTillBits(self.offenseCost)
        turnsTillDefense = self.player.TurnsTillCores(defenseCost)

        self.print("{} turns till offense, {} turns till defense".format(turnsTillOffense, turnsTillDefense))
        self.print("{} cores needed for ping cannon".format(defenseCost))

        
        if turnsTillDefense < 2 and turnsTillOffense < 2:
            self.notBuildAllowed , self.cleared = BuildingPlans.ClearForType(self.game_state,"pingCannon", self.side)
            self.currentCannonSide = self.side # now the side is fixed, no more changing it. # TODO: is this correct?

        if turnsTillDefense < 1 and turnsTillOffense < 1 and self.cleared:

            self.defenseBuilt = True
            self.notBuildAllowed = BuildingPlans.GetNotBuildAllowedByCannon(self.side)
            defenseCost = 0
            self.print("cannon built, ready to fire")
            self.allowedToChange = False
        else:
            # dont build cannon until you can afford it
            self.defenseUnits = []
            self.defenseBuilt = False


        # skip building a cannon if you're at high risk!
        if self.enemyThreatLevel<0.3: # VALUE find threshold
            self.defenseUnits = []
            self.print("CANNON: Delaying cannon, building adaptive instead!")


        # if cannon is built: spawn adaptive defense
        if defenseCost <= 0 or (defenseCost>0 and turnsTillDefense < 1 ): # this will screw me again?^^
            units, _ =  BuildingPlans.GetAdaptiveDefense(self.game_state,
            self.gameGrid,
            self.player,
                                                          self.enemy,
                                                          reversed = self.reversed,
                                                          useBottleNecks = False)

            self.defenseUnits += [i for i in units if i[0] not in self.notBuildAllowed]
            self.print(self.defenseUnits)
        # if i have enough cores, but am waiting for the pings:
        # this / should / already be the case, no?  



    #------------------------------------------------------------------
    def MazeDefense(self):
        #self.print("maze defense")
        self.defenseBuilt = False
        self.defenseUnits = BuildingPlans.GetMaze(self.game_state)
        self.notBuildAllowed, self.cleared = BuildingPlans.ClearForType(self.game_state, "maze")
        #self.print("maze cleared: ".format(self.cleared))
        self.missing = BuildingPlans.CheckIfBuilt(self.game_state,"maze") + 4 # TODO: that's BS...
        self.minCores = BuildingPlans.GetMinCoresForMaze()
        if self.missing<1:
            self.defenseBuilt = True
    #------------------------------------------------------------------
    def DeployDefense(self):
        #self.print("deploying defense")
        spawn = self.game_state.attempt_spawn

        # dont build defense if i don't have, save resources for ENCs instead!
        turnsTillOffense = self.player.TurnsTillBits(self.offenseCost)
        """
        if  self.enemyThreatLevel > 0.5 and self.game_state.turn_number>1: # VALUE find good threshold
            if turnsTillOffense==1:
                self.defenseUnits = []
        """
        #self.print(self.defenseUnits)
        """
        if self.enemyThreatLevel > 1.1 and self.name != "pingCannon": # value
            # dont bother w/ defense!
            self.defenseUnits = []
            self.print("skipping defense, enemyThreatlevel {}".format(self.enemyThreatLevel))
        """


        #self.print(self.defenseUnits)
        if turnsTillOffense < 1:
            self.defenseUnits = [i for i in self.defenseUnits if i[0] not in self.notBuildAllowed]
      

        # BUILD ENCRYPTORS

        # TODO: think about when to really spawn encs:
        # - threat levels low
        # - score high
        # . big offense (numOffenseTurns? len(offenseUnits)?))

        # right now: always spawning them if i have less than 7 and can afford them...?
       
        
        # BUILD DEFENSE
        #self.print(self.defenseUnits)
        for d in self.defenseUnits:
            spawned = spawn(d[1],d[0])
            if spawned > 0:
                self.print("DEFENSE: spawned {} at {}".format(d[1],d[0]))
        


        self.print("{}, {}, {}".format(turnsTillOffense, self.spawnEncryptors, len(self.offenseUnits)))

        if turnsTillOffense==0 and self.spawnEncryptors and len(self.offenseUnits)>0 :
            self.print("TRUUUEEEE")
            encryptorPoints = self.FindPointsForEncryptors(self.player.bestScore)
            self.SpawnEncryptors(encryptorPoints)

    #------------------------------------------------------------------
    def SpawnEncryptors(self,points):
        spawn = self.game_state.attempt_spawn
        delete = self.game_state.attempt_remove
        count = 0
        self.maxEncryptorsPerTurn = 99
        for point in points:
            if count > self.maxEncryptorsPerTurn:
                break
            spawned = spawn(self.game_state.ENCRYPTOR, point)
            count += 1
            if spawned>0:
                #pass
                delete(point)
            #    self.print("spawned Encryptor @ {}".format(point))
    #------------------------------------------------------------------
    def FindPointsForEncryptors(self,path):
        game_state = self.game_state
        ret = em_util.getPathAround(path.path, game_state, 1)
        ret = em_util.removeDuplicates(ret)
        ret = [point for point in ret if point[1] < 10 and point[1] > 2 and point not in path.path ] # slow?
        ret = [point for point in ret if self.game_state.can_spawn(self.game_state.ENCRYPTOR, point)]
        ret = [point for point in ret if point not in self.notBuildAllowed]
        ret = ret[:5]
        if path.value<1:
            ret = ret[:1] # minimalism
        return ret
    #------------------------------------------------------------------
    # UNUSED
    def CreateOffense(self):
        pass
    #------------------------------------------------------------------
    # deploy the default adaptive offense!
    def DeployOffense(self):
        if self.name == "pingCannon":
            self.PingCannonOffense()
        else:
            self.DefaultOffense()

    #------------------------------------------------------------------
    def DefaultOffense(self):
        unitCount = 0
        if self.player.bits >= self.offenseCost:
            #self.print(self.offenseUnits)
            for unit in self.offenseUnits:
                if self.name == "maze":
                    spawned = self.game_state.attempt_spawn(unit[0],unit[1])
                    unitCount+=spawned

                else:
                    spawned = self.game_state.attempt_spawn(unit[0],self.player.bestScore.startPoint)
                    unitCount+=spawned
                   
                     #so what if I still have bit's left here?
            spawned = self.game_state.attempt_spawn(self.game_state.PING,self.player.bestScore.startPoint,self.game_state.number_affordable(self.game_state.PING))
            if spawned>0:
                unitCount+=spawned
                #self.print("spawned {} PI from leftovers..!".format(spawned)) 

            self.offenseActive = False
            self.offenseUnits = []
            self.print("spawned {} offenseUnits".format(unitCount))
        #else:
        #    self.print("can't afford offense yet... {} / {}".format(self.offenseCost, self.player.bits))
    #------------------------------------------------------------------
    def PingCannonOffense(self):
        unitCount = 0
        spawn = self.game_state.attempt_spawn
        if self.defenseBuilt and self.player.bits > self.offenseCost:
            self.print("FIRING CANNON")
            self.allowedToChange = True
            for unit in self.offenseUnits:
                spawned = spawn(unit[0], BuildingPlans.GetPingCannonSpawn(self.currentCannonSide))
                unitCount+=spawned
            self.offenseActive = False

            # still bits left??
            spawned = spawn(self.game_state.PING,BuildingPlans.GetPingCannonSpawn(self.currentCannonSide), self.game_state.number_affordable(self.game_state.PING))
            unitCount +=spawned
            if spawned>0:
                self.print("spawned {} units for CANNON".format(unitCount))


    #------------------------------------------------------------------

    #------------------------------------------------------------------
    def SetCurrentStrategy(self, name, side, enemyThreatLevel, playerThreatLevel):
        self.enemyThreatLevel = enemyThreatLevel
        self.playerThreatLevel = playerThreatLevel
        if not self.allowedToChange:
            return 
        if self.name=="pingCannon":
            if name !="pingCannon": # strat changed - remove pingcannon
                BuildingPlans.RemovePingCannon(self.game_state,self.side)
                self.print("removing ping cannon...: {} :(".format(self.side))
                self.spawnEncryptors = True

        self.side = side

        if name=="pingCannon":
            self.name = name

        elif name == "maze":
            self.name = name
            self.side = "left" # override
            self.spawnPoint = [7,6] 

        else:
            self.name = "adaptive"


            #unitType, amount = self.enemy.PredictedSpawn()
            # TODO: maybe take /what/ the enemy wills pawn into account aswell

        



    #------------------------------------------------------------------
