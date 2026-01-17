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
        
    def getNextLandToCapture(self, game_message, team_id, my_team, ownership_grid, my_team_id, game_message_full):
        ownGrid = game_message.world.ownershipGrid
        nmap = game_message.world.map.nutrientGrid #Not the other one
        if self.landBase == []:
            initSpawn = my_team.spawners[0].position
            for x in range(len(nmap)):
                for y in range(len(nmap[x])):
                    if nmap[x][y] > 0:
                        self.landBase.append((x, y))
                        self.totalPossibleIncome += nmap[x][y]
                        
            self.landBase.sort(key=lambda pos: a_star((initSpawn.x, initSpawn.y), pos, ownership_grid, my_team_id, game_message_full) or float('inf'))
            
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
            
            nextPos = self.getNextLandToCapture(game_message, my_team.teamId, my_team, game_message.world.ownershipGrid, my_team.teamId, game_message)
            
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
                            position=Position(nextPos[0], nextPos[1])
                        ))
            else:
                print("Boros energy moment")
                if my_team.spores:
                    target_spawner = get_cheapest_spawner(my_team.spores[0], game_message.world.spawners, game_message.world.ownershipGrid, my_team.teamId, game_message)
                    if target_spawner:
                        for spore in my_team.spores:
                            actions.append(
                                SporeMoveToAction(
                                    sporeId=spore.id,
                                    position=target_spawner.position,
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


def get_neighbors(pos, grid_width, grid_height):
    x, y = pos
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    neighbors = []
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid_width and 0 <= ny < grid_height:
            neighbors.append((nx, ny))
    return neighbors


def a_star(start, goal, grid, my_team_id, game_message):
    from heapq import heappop, heappush
    open_set = []
    heappush(open_set, (0, start))  # Pas d'heuristique, utilise Dijkstra pour le chemin le moins coûteux
    came_from = {}
    g_score = {start: 0}
    closed = set()
    while open_set:
        _, current = heappop(open_set)
        if current in closed:
            continue
        closed.add(current)
        if current == goal:
            return g_score[current]
        for neighbor in get_neighbors(current, len(grid[0]), len(grid)):
            if neighbor in closed:
                continue
            nx, ny = neighbor
            owner = grid[ny][nx]
            cost = 1 if owner == my_team_id else game_message.world.biomassGrid[ny][nx]  # murs traversables mais plus coûteux
            tentative_g = g_score[current] + cost
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                heappush(open_set, (tentative_g, neighbor))  # Pas d'heuristique
    return None


def get_cheapest_spawner(spore, spawners, ownership_grid, my_team_id, game_message):
    cheapest_spawner = None
    cheapest_cost = float('inf')
    start = (spore.position.x, spore.position.y)
    for spawner in spawners:
        if spawner.teamId == my_team_id:
            continue
        goal = (spawner.position.x, spawner.position.y)
        cost = a_star(start, goal, ownership_grid, my_team_id, game_message)
        if cost is not None and cost < cheapest_cost:
            cheapest_cost = cost
            cheapest_spawner = spawner
    return cheapest_spawner