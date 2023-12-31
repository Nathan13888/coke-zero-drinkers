import random
from sys import maxsize
import json
import os
import sys

from typing import List, Tuple, Any, Literal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# pylint: disable=wrong-import-position
# pylint: disable=E0401
import gamelib

# Most of the algo code you write will be in this file unless you create new
# modules yourself. Start by modifying the 'on_turn' function.

# Advanced strategy tips: 

#   - You can analyze action frames by modifying on_action_frame function

#   - The GameState.map object can be manually manipulated to create hypothetical 
#   board states. Though, we recommended making a copy of the map to preserve 
#   the actual current map state.
# """


class AlgoStrategy(gamelib.AlgoCore):
    """
    Coke-Zero-Drinkers Strategy
    """
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write("Random seed: {}".format(seed))

        self.scored_on_locations = []
        self.development_plan: List[Tuple[Any, List[List[int]], Literal["BUILD", "BUILD_UPGRADE", "REFUND"]]] = []

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write("Configuring your custom algo strategy...")
        self.config = config
        # pylint: disable=W0601
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"] # pyright: ignore[reportGeneralTypeIssues]
        SUPPORT = config["unitInformation"][1]["shorthand"] # pyright: ignore[reportGeneralTypeIssues]
        TURRET = config["unitInformation"][2]["shorthand"] # pyright: ignore[reportGeneralTypeIssues]
        SCOUT = config["unitInformation"][3]["shorthand"] # pyright: ignore[reportGeneralTypeIssues]
        DEMOLISHER = config["unitInformation"][4]["shorthand"] # pyright: ignore[reportGeneralTypeIssues]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"] # pyright: ignore[reportGeneralTypeIssues]
        
        MP = 1
        SP = 0

        # Log configs
        gamelib.debug_write("CONFIGS")
        gamelib.debug_write(f"WALL: {WALL}")
        gamelib.debug_write(f"SUPPORT: {SUPPORT}")
        gamelib.debug_write(f"TURRET: {TURRET}")
        gamelib.debug_write(f"SCOUT: {SCOUT}")
        gamelib.debug_write(f"DEMOLISHER: {DEMOLISHER}")
        gamelib.debug_write(f"INTERCEPTOR: {INTERCEPTOR}")
        # This is a good place to do initial setup
        # TODO: ascii art - https://emojicombos.com/coca-cola-zero

        ###############################################

        # Walls of initial structure
        left_ledge = [[0, 13], [1, 13], [3, 13]] # LEFT FRONT
        right_ledge = [[27, 13], [26, 13], [25, 13], [24, 13], [23, 13]] # RIGHT FRONT
        left_flank = [[1, 12], [2, 12], [3, 11], [4, 10], [5, 9], [6, 8], [7, 7]] # LEFT WALL
        right_flank = [[21, 10], [20, 9], [19, 8], [18, 7], [17, 6], [8, 6]] # RIGHT WALL
        belly = [[9, 5], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [16, 5]] # BOTTOM FLAT PART
        initial_walls = [*left_ledge, *right_ledge, *left_flank, *belly, *right_flank]
        guide_walls = [[22, 13], [22, 12], *[[21 - x, 13] for x in range(3)]] # GUIDE + EXTRA TURRET POTECTION

        # Upgraded turrets of initial structure
        initial_upgraded_turrets = [[2, 13], [22, 10]]
        # Turrets of initial structure
        initial_turrets = [[23, 12], [24, 12], [25, 12], [21, 9], [20, 8]]
        surround1_turrets = [[2, 11], [18, 6], [4, 9], [16, 4], [6, 7], [8, 5]]
        surround2_turrets = [[10, 4], [14, 4], [12, 4]]

        # Threshold to refund damaged walls in percentage TODO
        # damaged_wall_threshold = 50 # 50%

        # Plan for structures
        self.development_plan = [
            # Build initial structure
            (WALL, initial_walls, "BUILD"),
            (TURRET, initial_upgraded_turrets, "BUILD"),
            (TURRET, initial_turrets, "BUILD"),
            (TURRET, initial_upgraded_turrets, "BUILD_UPGRADE"),
            (SUPPORT, [[24, 11]], "BUILD"),

            # Upgrade initial structure
            (TURRET, guide_walls, "BUILD_UPGRADE"),
            (TURRET, initial_turrets, "BUILD_UPGRADE"),
            (WALL, right_ledge, "BUILD_UPGRADE"),
            (SUPPORT, [[24, 11]], "BUILD_UPGRADE"),
            (SUPPORT, [[24, 10]], "BUILD_UPGRADE"),

            # Late game (lots of resources)
            (WALL, right_ledge, "BUILD_UPGRADE"),
            (WALL, left_ledge, "BUILD_UPGRADE"),
            (WALL, right_flank, "BUILD_UPGRADE"),
            (SUPPORT, [[20, 10]], "BUILD_UPGRADE"),

            # Build and upgrade final upgrades, complete surrounding
            (SUPPORT, [[19, 7]], "BUILD_UPGRADE"),
            (TURRET, surround1_turrets, "BUILD"),
            (WALL, left_flank, "BUILD_UPGRADE"),
            (TURRET, surround2_turrets, "BUILD"),
            (WALL, belly, "BUILD_UPGRADE"),

            (TURRET, surround1_turrets, "BUILD_UPGRADES"),
            (TURRET, surround2_turrets, "BUILD_UPGRADES"),
        ]

        gamelib.debug_write("DEVELOPMENT PLAN")
        gamelib.debug_write(self.development_plan)

    def on_turn(self, game_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, game_state)
        gamelib.debug_write(
            f"Performing turn {game_state.turn_number} of your custom algo strategy"
        )
        game_state.suppress_warnings(True)

        # TODO: cProfile, pstats

        self.strategy(game_state)

        game_state.submit_turn()

    def strategy(self, game_state: gamelib.GameState):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """

        # Defence
        self.build_defences(game_state)

        # Offence
        self.execute_offence(game_state)

    def build_defences(self, game_state: gamelib.GameState):
        """
        Builds defences that are predetermined and preemptively placed
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
        
        # Only build defences after turn 1, skipping turn 0
        if game_state.turn_number >= 1:
            # Build basic defenses using hardcoded locations.
            # Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
            
            # Execute development plan
            for structure, points, action in self.development_plan:
                if action == 'BUILD':
                    build_count = game_state.attempt_spawn(structure, points)
                    gamelib.debug_write(f"Built {build_count} {structure} at {points}.")
                elif action == 'BUILD_UPGRADE':
                    build_count = game_state.attempt_spawn(structure, points)
                    gamelib.debug_write(f"Built {build_count} {structure} at {points}.")
                    upgrade_count = game_state.attempt_upgrade(points)
                    gamelib.debug_write(f"Upgraded {upgrade_count} {structure} at {points}.")
                else:
                    # Refund means delete if it's below certain threshold and rebuild (only if you could afford it)
                    # TODO
                    gamelib.debug_write("WARNING: Refund not implemented yet.")


            # # Build walls
            # built_wall = game_state.attempt_spawn(WALL, self.pink_filters_points)
            # # Build turrets
            # built_upgraded_turrets = game_state.attempt_spawn(TURRET, self.blue_destructors_points)
            # built_turrets = game_state.attempt_spawn(TURRET, self.pink_destructors_points)
            # # Upgrade turrets
            # upgraded_upgraded_turrets = game_state.attempt_upgrade(self.blue_destructors_points)

            # gamelib.debug_write(f"Built {built_wall} walls.")
            # gamelib.debug_write(f"Built {built_upgraded_turrets} upgraded turrets.")
            # gamelib.debug_write(f"Built {built_turrets} turrets.")
            # gamelib.debug_write(f"Upgraded {upgraded_upgraded_turrets} upgraded turrets.")

            # Continue building if there are still SP resources
            # if game_state.get_resource(SP) > 0:

            # TODO

            # Build initial structure

            # Repair initial structure

            # Upgrade structure



            # game_state.attempt_spawn(TURRET, turret_locations)

            # self.build_reactive_defence(game_state)
        
            # TODO: Delete structures to get back points

    def build_reactive_defence(self, game_state: gamelib.GameState):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        # TODO: Add debug traces
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1] + 1]
            game_state.attempt_spawn(TURRET, build_location)

#######################################################################################################################
##################################################  Helpers ###########################################################
#######################################################################################################################

    def stall_with_interceptors(self, game_state: gamelib.GameState):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        # pyright: ignore[reportGeneralTypeIssues]
        friendly_edges = game_state.game_map.get_edge_locations( # pyright: ignore[reportGeneralTypeIssues]
            game_state.game_map.BOTTOM_LEFT
        ) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        # While we have remaining MP to spend lets send out interceptors randomly.
        while (
            game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP]
            and len(deploy_locations) > 0
        ):
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            
            # We don't have to remove the location since multiple mobile 
            # units can occupy the same space.

    def demolisher_line_strategy(self, game_state: gamelib.GameState):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if (
                unit_class.cost[game_state.MP]
                < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]
            ):
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += (
                    len(game_state.get_attackers(path_location, 0))
                    * gamelib.GameUnit(TURRET, game_state.config).damage_i
                )
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        """
        Determines whether or not the enemy has a unit of a certain type.
        """
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if (
                        unit.player_index == 1
                        and (unit_type is None or unit.unit_type == unit_type)
                        and (valid_x is None or location[0] in valid_x)
                        and (valid_y is None or location[1] in valid_y)
                    ):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state: gamelib.GameState):
        """
        Remove locations that are blocked by our own structures.
        """
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    # TODO: Justin what is this??
    def on_action_frame(self, turn_string: str):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write(
                    "All locations: {}".format(self.scored_on_locations)
                )
    
    def build_preemptive_defense(self, game_state: gamelib.GameState):
        """
        Simulates every single possible path an enemy could take if they used all scouts,
        interceptors, or demolisher and determine the paths they traversed the most.
        """
        # Dictionary to store the frequency of each path
        path_frequency = {}

        # Define the enemy unit types to simulate
        # enemy_unit_types = [game_state.SCOUT, game_state.DEMOLISHER, game_state.INTERCEPTOR]

        # Iterate through each enemy unit type

        for x in range(game_state.ARENA_SIZE):
            start_location = (x, game_state.ARENA_SIZE - 1)  # Assuming enemy spawns at the top edge
            target_edge = game_state.get_target_edge(start_location)

            # Get the path the unit would take
            path = game_state.find_path_to_edge(start_location, target_edge)

            if path is not None:
                # Increment the frequency count for each location in the path
                for location in path:
                    if location in path_frequency:
                        path_frequency[location] += 1
                    else:
                        path_frequency[location] = 1

        # Find the most frequently traversed locations
        most_traversed_locations = sorted(path_frequency, key=path_frequency.get, reverse=True)

        # Build TURRET or other defensive structures at the most traversed locations
        for location in most_traversed_locations[:5]: # Adjust the number of locations as needed
            if game_state.can_spawn(game_state.TURRET, location):
                game_state.attempt_spawn(game_state.TURRET, location)


#######################################################################################################################
################################################### Offence ###########################################################
#######################################################################################################################

    def execute_offence(self, game_state: gamelib.GameState):
        """
        Executes offence based on the current game state
        """

        # TUNABlES
        detected_enemy_units_threshold = 8
        stall_turns = 1
        min_spam_scout_threshold = 5
        spam_scout_threshold = 30
        def_spawn_loc = [22, 8]
        # TODO: check if spawn loc has shit
        saved_mp = 4

        mobile_budget = game_state.get_resources()[1]
        opponent_sp = game_state.get_resources(player_index=1)[0]
        opp_sp_min_threshold = 8

        gamelib.debug_write(f"BUDGET: MOBILE_POINTS, {mobile_budget} points")

        ######################################

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < stall_turns:
            # self.stall_with_interceptors(game_state)
            # "quick ping" - catch 'em off guard
            # TODO: check if this works
            
            random_locations = [[13, 0], [14, 0], [0, 13], [27, 13]]
            random_location = random.choice(random_locations)
            count = int(mobile_budget)
            game_state.attempt_spawn(SCOUT, random_location, count)
            gamelib.debug_write(f"SPAWN: STALLING, SPAM_SCOUT, {count} count")
            return
        

        # TODO: consider all paths to spawn

        if (mobile_budget >= spam_scout_threshold or
            (# they are vulnerable??
            # if they have fewer than the threshold number of structures
            self.detect_enemy_unit(
                game_state, unit_type=None,
                valid_x=[x for x in range(14)],
                valid_y=None,
            )
            # detect units on the left side (top-left quadrant)
            # self.detect_enemy_unit(
            #     game_state, unit_type=None,
            #     valid_x=[x for x in range(14)],
            #     valid_y=[y+14 for y in range(14)],
            # )
            < detected_enemy_units_threshold
            and mobile_budget >= min_spam_scout_threshold
            and opponent_sp < opp_sp_min_threshold
            )
        ):

            # TODO: sort out demolisher_line_strategy
            # self.demolisher_line_strategy(game_state)
            # TODO: "stage" an attack, require support, place intercepters in front?
            count = int(mobile_budget)
            game_state.attempt_spawn(SCOUT, def_spawn_loc, count)
            gamelib.debug_write(f"SPAWN: SPAM_SCOUT, {count} count")

        else:
            # TODO: detect if there's a path for SPAM_SCOUT
            if game_state.turn_number % 2 == 1:
                gamelib.debug_write("(SKIPPING) SPAWN")
                return
            
            # TODO: figure out where to spawn scouts + how many
            # game_state.config["unitInformation"][4]["cost2"]
            cost_of_demolisher = 3 # TODO: get from config
            count = int((mobile_budget - saved_mp) / cost_of_demolisher) # max number of scouts to spawn per push
            
            game_state.attempt_spawn(DEMOLISHER, def_spawn_loc, count)

            gamelib.debug_write(f"SPAWN: SPAM_DEMOLISHER, {count} count")
        
        # They don't have many units in the front so lets figure out their least defended area and send Scouts there.
        # - spawn scouts every odd turn
        # - spam to protect self
        # cost_of_interceptor = 2 # TODO: get from config

        # mid_spawn_loc = [20, 6]
        rear_spawn_loc = [18, 4]

        # game_state.attempt_spawn(INTERCEPTOR, mid_spawn_loc, 1)
        # game_state.attempt_spawn(SCOUT, rear_spawn_loc, saved_mp - cost_of_interceptor)
        # TODO: revisit effectiveness of interceptors
        game_state.attempt_spawn(SCOUT, rear_spawn_loc, saved_mp)
        
        # TODO: log this??
        




#######################################################################################################################

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
