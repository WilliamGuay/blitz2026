import random
from game_message import *


class Bot:
    def __init__(self):
        print("Initializing your super mega duper bot")

    def get_next_move(self, game_message: TeamGameState) -> list[Action]:
        """
        Here is where the magic happens, for now the moves are not very good. I bet you can do better ;)
        """
        actions = []

        my_team: TeamInfo = game_message.world.teamInfos[game_message.yourTeamId]
        if len(my_team.spawners) == 0:
            actions.append(SporeCreateSpawnerAction(sporeId=my_team.spores[0].id))

        elif len(my_team.spores) == 0 and my_team.nutrients >= 20:
            actions.append(
                SpawnerProduceSporeAction(spawnerId=my_team.spawners[0].id, biomass=20)
            )

        else:
            if my_team.nutrients >= 10:
                actions.append(SpawnerProduceSporeAction(spawnerId=my_team.spawners[0].id, biomass=10))
                
            for spore in my_team.spores:
                if spore.biomass > 2:
                    
                    actions.append(
                        SporeMoveToAction(
                            sporeId=spore.id,
                            position=get_direct_move(spore, get_closest_spawner(spore, game_message.world.spawners).position),
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