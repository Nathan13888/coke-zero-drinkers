from gamelib import debug_write
from sys import stderr

#------------------------------------------------------------------
def print(msg):
    LOG.append([msg])
    if ACTIVE:
        debug_write(msg)
#------------------------------------------------------------------
def dumpLog():
    if not DUMPLOG:
        return
    for msg in LOG:
        debug_write("'{}'".format(msg[0]))
#------------------------------------------------------------------
def print_scores(scores):
    allPaths = []
    for score in scores:
        #allPaths.append(score.endPoint)
        for point in score.path:
            allPaths.append(point)
    #allPaths = playerScores[0].path
    cords = []
    vals = []
    for point in allPaths:
        if point in cords:
            index = cords.index(point)
            vals[index]+=1
        else:
            cords.append(point)
            vals.append(1)
    map = [[vals[x],cords[x]] for x in range(len(cords))]


    vals = [x[0] for x in map]
    cords= [x[1] for x in map]
    for y in range(28):
        for x in range(28):
            thisCord = [x,27-y]

            if thisCord in cords:
                index = cords.index(thisCord)
                _print_justified(vals[index])
            else:
                stderr.write("   ")
        stderr.write("\n")
#------------------------------------------------------------------
def print_path(path, game_map):
    pos = 0
    arena = game_map.get_all_locations()
    for y in range(28):
        for x in range(28):

            thisCord = [x,27-y]
            #if not thisCord in arena:
            #   continue
            if thisCord in path:
                # _print_justified(pos)
                stderr.write(" o ")
                pos+=1
            elif  game_map[thisCord]:
                if game_map[thisCord][0].stationary:
                    stderr.write(" x ")
            elif thisCord in arena:
                stderr.write(" . ")
            else:
                stderr.write("   ")
        stderr.write("\n")
#------------------------------------------------------------------
def print_values_dict(vals,game_map,scaling = True):
    from math import log
    scale = 1
    if scaling: 
        scale = max(vals.values())*99
    else:
        scale = 1
    for y in range(28):
        for x in range(28):
            thisCord = (x,27-y)
            #if not thisCord in arena:
            #   continue
            if thisCord in vals:
                _print_justified(int((vals[thisCord])/scale))

            elif game_map[thisCord]:
                if game_map[thisCord][0].stationary:
                    stderr.write(" . ")

            else:
                stderr.write("   ")
        stderr.write("\n")



def print_map(map):
    pass  # TODO:
#------------------------------------------------------------------
def _print_justified(number):
    """Prints a number between 100 and -10 in 3 spaces
    """
    if number < 10 and number > -1:
        stderr.write(" ")
    stderr.write(str(number))
    stderr.write(" ")



LOG = []
ACTIVE = True
DUMPLOG = False
PREFIX = ""

if __name__ == "__main__":
    print("hello")
    print("..")
    dumpLog()
