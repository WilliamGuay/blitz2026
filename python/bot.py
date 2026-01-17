import random
from game_message import *

ROLES = []

class Bot:
    
    def __init__(self):
        self.landBase = []      
        self.targetNutrients = []
        self.totalPossibleIncome = 0
        
    def getNextLandToCapture(self, game_message, team_id):
        ownGrid = game_message.world.ownershipGrid
        for n in self.landBase:
            if ownGrid[n[0], n[1]] != team_id:
                return n
        
        return (-1, -1)

    def get_next_move(self, game_message: TeamGameState) -> list[Action]:
        actions = []
        my_team: TeamInfo = game_message.world.teamInfos[game_message.yourTeamId]


        if len(my_team.spawners) == 0:
            actions.append(SporeCreateSpawnerAction(sporeId=my_team.spores[0].id))

        if len(self.landBase) == 0 and not len(my_team.spawners) == 0:
            nmap = game_message.world.map.nutrientGrid #Not the other one
            initSpawn = my_team.spawners[0].position
            for x in range(len(nmap)):
                for y in range(len(nmap[x])):
                    if nmap[x][y] > 0:
                        self.landBase.append((x, y))
                        self.totalPossibleIncome += nmap[x][y]
                        
            self.landBase.sort(key=lambda pos: abs(pos[0] - initSpawn.x) + abs(pos[1] - initSpawn.y))
            
        elif len(my_team.spores) == 0:
            actions.append(
                SpawnerProduceSporeAction(spawnerId=my_team.spawners[0].id, biomass=20)
            )

        else:
            
            
            if my_team.nutrients >= 10:
                actions.append(SpawnerProduceSporeAction(spawnerId=my_team.spawners[0].id, biomass=10))
                
            for spore in my_team.spores:
                if spore.biomass > 2:
                    for spawner in game_message.world.spawners:
                        if spawner.teamId != game_message.yourTeamId:
                            actions.append(
                                SporeMoveToAction(
                                    sporeId=spore.id,
                                    position=spawner.position,
                                )
                            )
                            break
        return actions
