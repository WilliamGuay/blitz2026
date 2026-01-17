import random
from game_message import *

ROLES = []

class Bot:
    
    def __init__(self):
        self.landBase = []      
        self.targetNutrients = []
        self.totalPossibleIncome = 0
        self.InitialSpawnPos = (-1, -1)
        self.currentProd = 0
        
    def getNextLandToCapture(self, game_message, team_id, my_team):
        ownGrid = game_message.world.ownershipGrid
        nmap = game_message.world.map.nutrientGrid #Not the other one
        if self.landBase == []:
            initSpawn = my_team.spawners[0].position
            for x in range(len(nmap)):
                for y in range(len(nmap[x])):
                    if nmap[x][y] > 0:
                        self.landBase.append((x, y))
                        self.totalPossibleIncome += nmap[x][y]
                        
            self.landBase.sort(key=lambda pos: abs(pos[0] - initSpawn.x) + abs(pos[1] - initSpawn.y))
            
        for n in self.landBase:
            if ownGrid[n[0]][n[1]] == team_id:
                self.currentProd += nmap[n[0]][n[1]]
            
        for n in self.landBase:
            if ownGrid[n[0]][n[1]] != team_id:
                return n
        
        return (-1, -1)

    def get_next_move(self, game_message: TeamGameState) -> list[Action]:
        self.currentProd = 0
        actions = []
        my_team: TeamInfo = game_message.world.teamInfos[game_message.yourTeamId]


        if len(my_team.spawners) == 0:
            actions.append(SporeCreateSpawnerAction(sporeId=my_team.spores[0].id))
            
        if my_team.nutrients >= 20:
            actions.append(
                SpawnerProduceSporeAction(spawnerId=my_team.spawners[0].id, biomass=20)
            )

        elif len(my_team.spawners) > 0:
            
            nextPos = self.getNextLandToCapture(game_message, my_team.teamId, my_team)
            
            if my_team.nutrients >= 10:
                actions.append(SpawnerProduceSporeAction(spawnerId=my_team.spawners[0].id, biomass=10))
            
            print(self.currentProd, self.totalPossibleIncome / 3)
            if self.currentProd < self.totalPossibleIncome / 3:
                print("building economy")
                for spore in my_team.spores:
                    if nextPos == (-1, -1):
                        pass
                    else:
                        actions.append(SporeMoveToAction(
                            sporeId=spore.id,
                            position=get_direct_move(spore, Position(nextPos[0], nextPos[1]))
                        ))
            else:
                print("Boros energy moment")
                for spore in my_team.spores:
                    actions.append(
                        SporeMoveToAction(
                            sporeId=spore.id,
                            position=get_direct_move(spore, get_closest_spawner(spore, game_message.world.spawners)),
                        )
                    )
        return actions

def get_closest_spawner(spore: Spore, spawners: list[Spawner]) -> Spawner:
    closest_spawner = None
    closest_distance = float('inf')
    for spawner in spawners:
        if spawner.teamId == spore.teamId:
            continue
        distance = ((spore.position.x - spawner.position.x) ** 2 + (spore.position.y - spawner.position.y) ** 2) ** 0.5
        if distance < closest_distance:
            closest_distance = distance
            closest_spawner = spawner
    return closest_spawner

def get_direct_move(spore: Spore, destination: Position) -> Position:
    if destination is None:
        return spore.position
    
    dx = destination.x - spore.position.x
    dy = destination.y - spore.position.y
    
    if dx == 0 and dy == 0:
        return destination
    
    step_x = (1 if dx > 0 else -1) if abs(dx) >= abs(dy) else 0
    step_y = (1 if dy > 0 else -1) if abs(dy) > abs(dx) else 0
    return Position(
        x=spore.position.x + step_x,
        y=spore.position.y + step_y,
    )