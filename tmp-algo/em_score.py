class Score:
    def __init__(
        self,
        path=[],
        value = 0,
        health = 0,
        units = [],
        pathToEnd = False,
        lengthInEnemyTerritory = 0,
        valueNearSpawn = 0, valueNearBreach = 0,
        unitsNearSpawn = [], unitsNearBreach=[],healthNearBreach = 0,healthNearSpawn = 0
        ):

        self.path = path
        self.pathLength = len(path)
        self.value = value
        self.health = health
       
        self.units = units
        self.startPoint = path[0]
        self.endPoint = path[-1]
        self.pathToEnd = pathToEnd
        self.lengthInEnemyTerritory = lengthInEnemyTerritory
        self.valueNearSpawn = valueNearSpawn
        self.valueNearBreach = valueNearBreach
        self.unitsNearSpawn = unitsNearSpawn
        self.unitsNearBreach = unitsNearBreach
        self.healthNearSpawn = healthNearSpawn
        self.healthNearBreach = healthNearBreach


