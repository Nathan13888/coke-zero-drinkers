# pylint: disable=wrong-import-position,wrong-import-order,unused-import
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import gamelib
import random
import math
import warnings
import json
import copy
from sys import maxsize
from collections import Counter
import time
from typing import Optional

from em_timer import Timer

from em_brain import Brain






#------------------------------------------------------------------
class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        random.seed()
        self.brain = Brain()
        self.game_state: Optional[gamelib.GameState] = None
        self.timer = Timer()
        self.turnTimer = Timer()
        self.turnCount = 0
    #------------------------------------------------------------------
    def on_game_start(self, config):
        self.config = config
        gamelib.debug_write("Brain Active -> CONFIG DONE.")

        self.timer.reset()


    #------------------------------------------------------------------
    def on_turn(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)
        self.turnTimer.reset()
        self.turnCount = game_state.turn_number
        self.game_state = game_state
        #game_state.suppress_warnings(True)
        game_state.enable_warnings = False

        if game_state.turn_number==0:
            self.brain.start(game_state)


        #import cProfile, pstats, io
        #from pstats import SortKey
        #pr = cProfile.Profile()
        #pr.enable()


        self.brain.update(game_state)

        #pr.disable()
        #ps = pstats.Stats(pr, stream=io.StringIO()).sort_stats(SortKey.CUMULATIVE)
        #ps.dump_stats('scripts/stats.dmp')



        #time.sleep(1) # DEBUG:
        game_state.submit_turn()
    #------------------------------------------------------------------
    def on_action(self,turn_state):
        #gamelib.debug_write("parsing action state")
        state = json.loads(turn_state)
        #self.brain.actionState = state # storing the complete action state

        self.brain.hits = []
        self.brain.enemyHitPoints = []
        self.brain.damage = []


        if(state["events"]["breach"]):
            self.brain.hits = [item for item in state["events"]["breach"] if item[0][1]<14]
            self.brain.enemyHitPoints += [item for item in self.brain.hits if item not in self.brain.enemyHitPoints]

        if(state["events"]["damage"]):
            tmpDamage = state["events"]["damage"]
            self.brain.damage = [item for item in tmpDamage if item[0][1]<14]
        if(state["events"]["melee"]):
            tmpDamage = state["events"]["melee"]
            self.brain.damage+=[item for item in tmpDamage if item[0][1]<14]
        if(state["events"]["attack"]):
            tmpDamage = state["events"]["attack"]
            self.brain.damage+=[item for item in tmpDamage if item[0][1]<14]
        if(state["events"]["death"]):
            tmpDamage = state["events"]["death"]
            self.brain.damage+=[item for item in tmpDamage if item[0][1]<14]

        if(state["events"]["spawn"]):
            enemyUnits = []
            playerUnits = []

            for line in state["events"]["spawn"]:
                type = self.GetUnitTypeFromID(line[1])
                if type:
                    if(line[0][1] > 13): # only enemy units
                        enemyUnits.append(gamelib.GameUnit(type, self.config, 1, None, line[0][0],line[0][1]))
                    else: # only player Units
                        playerUnits.append(gamelib.GameUnit(type, self.config, 1, None, line[0][0],line[0][1]))
            self.brain.enemyUnits.append(enemyUnits)
            self.brain.playerUnits.append(playerUnits)
    #------------------------------------------------------------------------------
    def GetUnitTypeFromID(self,ID):
        if self.game_state is None:
            return None

        if ID==0:
            return self.game_state.WALL
        if ID==1:
            return self.game_state.SUPPORT
        if ID==2:
            return self.game_state.TURRET
        if ID==3:
            return self.game_state.SCOUT
        if ID==4:
            return self.game_state.DEMOLISHER
        if ID==5:
            return self.game_state.INTERCEPTOR
        return None # -> could be a "remove unit thing, but that get's updated from game_state, so i can ignore it here"

    #------------------------------------------------------------------------------
    def on_end(self,turn_state):
        gs = gamelib.GameState(self.config, turn_state)
        self.brain.dumpLog()
        gamelib.debug_write("--------------------------")
        gamelib.debug_write("Average time per turn:  {:.2f} seconds".format(self.timer.timePassed()/(self.turnCount+1)))
        gamelib.debug_write("--------------------------")
        if gs.my_health>gs.enemy_health:
            gamelib.debug_write("PLAYER WON")
        elif gs.my_health<gs.enemy_health:
            gamelib.debug_write("o. O")
            gamelib.debug_write("O .o")
            gamelib.debug_write("Ó.Ò")
            gamelib.debug_write("PLAYER LOST")
        else:
            gamelib.debug_write("... not quite sure who won? o. O")
        gamelib.debug_write("{} : {}".format(gs.my_health,gs.enemy_health))
        gamelib.debug_write("gg! :)")
        #self.printArt()

    #------------------------------------------------------------------
    def printArt(self):
        #gamelib.debug_write(".  _   _ _____ _     _     ___  ")
        #gamelib.debug_write(". | | | | ____| |   | |   / _ \\ ")
        #gamelib.debug_write(". | |_| |  _| | |   | |  | | | |")
        #gamelib.debug_write(". |  _  | |___| |___| |__| |_| |")
        #gamelib.debug_write(". |_| |_|_____|_____|_____\\___/ ")
        gamelib.debug_write("")
        gamelib.debug_write("")
        gamelib.debug_write('.                               .oMc')
        gamelib.debug_write('.                            .MMMMMP')
        gamelib.debug_write('.                          .MM888MM')
        gamelib.debug_write('.    ...                 .MM88888MP')
        gamelib.debug_write('.    MMMMMMMMb.         d8MM8tt8MM')
        gamelib.debug_write('.     MM88888MMMMc `:´ dMME8ttt8MM')
        gamelib.debug_write('.      MM88tt888EMMc:dMM8E88tt88MP')
        gamelib.debug_write('.       MM8ttt888EEM8MMEEE8E888MC')
        gamelib.debug_write('.       `MM888t8EEEM8MMEEE8t8888Mb')
        gamelib.debug_write('.       "MM88888tEM8"MME88ttt88MM')
        gamelib.debug_write('.        dM88ttt8EM8"MMM888ttt8MM')
        gamelib.debug_write('.        MM8ttt88MM" " "MMNICKMM"')
        gamelib.debug_write('.        3M88888MM"      "MMMP"')
        gamelib.debug_write('.         "MNICKM"')
        gamelib.debug_write("")
        gamelib.debug_write("")
#------------------------------------------------------------------
if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
#------------------------------------------------------------------
