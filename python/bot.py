import random
from game_message import *
from heapq import heappop, heappush


ROLES = []

class Bot:
    
    def __init__(self):
        self.landBase = []      
        self.targetNutrients = []
        self.totalPossibleIncome = 0
        self.currentProd = 0
        
    def getNextLandToCapture(self, game_message, team_id, my_team, ownership_grid, my_team_id, game_message_full):
        ownGrid = game_message.world.ownershipGrid
        nmap = game_message.world.map.nutrientGrid #Not the other one
        if self.landBase == []:
            for x in range(len(nmap)):
                for y in range(len(nmap[x])):
                    if nmap[x][y] > 0:
                        self.landBase.append((x, y))
                        self.totalPossibleIncome += nmap[x][y]
                        
            self.landBase.sort(key=lambda pos: ((pos[0] - my_team.spawners[0].position.x)**2 + (pos[1] - my_team.spawners[0].position.y)**2)**0.5)
            
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
            if self.currentProd < self.totalPossibleIncome / 4:
                print("building economy")
                for spore in my_team.spores:
                    if nextPos == (-1, -1):
                        pass
                    else:
                        path = a_star((spore.position.x, spore.position.y), nextPos, game_message.world.ownershipGrid, my_team.teamId, game_message, avoid_bushes=True)
                        # Dernier recours : traverser les buissons si aucun chemin n'existe
                        if not path:
                            path = a_star((spore.position.x, spore.position.y), nextPos, game_message.world.ownershipGrid, my_team.teamId, game_message, avoid_bushes=False)
                        if path and len(path) > 1:
                            next_pos = path[1] 
                            print("nextPos:", nextPos)
                            print("pos: ", spore.position)
                            dx = next_pos[0] - spore.position.x
                            dy = next_pos[1] - spore.position.y
                            
                            dx = dx / (abs(dx) if dx != 0 else 1)
                            dy = dy / (abs(dy) if dy != 0 else 1)
                            
                            if dx != 0 and dy != 0:
                                dy = 0
                            
                            print("next move: ", (dx, dy))
                            actions.append(SporeMoveAction(
                                sporeId=spore.id,
                                direction=Position(dx, dy)
                            ))
            else:
                print("Boros energy moment")
                target_spawner = get_cheapest_spawner(my_team.spores[0], game_message.world.spawners, game_message.world.ownershipGrid, my_team.teamId, game_message)
                if target_spawner:
                    target_pos = (target_spawner.position.x, target_spawner.position.y)
                    path = a_star((my_team.spores[0].position.x, my_team.spores[0].position.y), target_pos, game_message.world.ownershipGrid, my_team.teamId, game_message, avoid_bushes=True)
                    # Dernier recours : traverser les buissons si aucun chemin n'existe
                    if not path:
                        path = a_star((my_team.spores[0].position.x, my_team.spores[0].position.y), target_pos, game_message.world.ownershipGrid, my_team.teamId, game_message, avoid_bushes=False)
                    if path and len(path) > 1:
                        next_pos = path[1]
                        dx = next_pos[0] - my_team.spores[0].position.x
                        dy = next_pos[1] - my_team.spores[0].position.y
                        
                        dx = dx / (abs(dx) if dx != 0 else 1)
                        dy = dy / (abs(dy) if dy != 0 else 1)
                        
                        if dx != 0 and dy != 0:
                            dy = 0
                        for spore in my_team.spores:
                            actions.append(SporeMoveAction(
                                sporeId=spore.id,
                                direction=Position(dx, dy)
                            ))
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

def get_neighbors(pos, grid_width, grid_height):
    x, y = pos
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    neighbors = []
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid_width and 0 <= ny < grid_height:
            neighbors.append((nx, ny))
    return neighbors


def a_star(start, goal, grid, my_team_id, game_message, avoid_bushes=True):
    open_set = []
    heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    closed = set()
    iterations = 0
    max_iterations = 1000
    while open_set and iterations < max_iterations:
        iterations += 1
        _, current = heappop(open_set)
        if current in closed:
            continue
        closed.add(current)
        if current == goal:
            path = [goal]
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        for neighbor in get_neighbors(current, len(grid[0]), len(grid)):
            if neighbor in closed:
                continue
            nx, ny = neighbor
            owner = grid[nx][ny]
            biomass = game_message.world.biomassGrid[nx][ny]
            
            if owner == my_team_id:
                cost = 1
            else:
                # Si on doit éviter les buissons, appliquer une très forte pénalité
                if avoid_bushes and biomass > 0:
                    cost = 1000 + biomass  # Très coûteux mais pas infini pour dernier recours
                else:
                    cost = biomass + 1
            
            tentative_g = g_score[current] + cost
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                heappush(open_set, (tentative_g, neighbor))
    return None


def get_cheapest_spawner(spore, spawners, ownership_grid, my_team_id, game_message):
    cheapest_spawner = None
    cheapest_cost = float('inf')
    start = (spore.position.x, spore.position.y)
    for spawner in spawners:
        if spawner.teamId == my_team_id:
            continue
        goal = (spawner.position.x, spawner.position.y)
        # D'abord, essayer d'éviter les buissons
        path = a_star(start, goal, ownership_grid, my_team_id, game_message, avoid_bushes=True)
        # Dernier recours : traverser les buissons si aucun chemin n'existe
        if not path:
            path = a_star(start, goal, ownership_grid, my_team_id, game_message, avoid_bushes=False)
        
        if path is not None:
            cost = len(path)
            if cost < cheapest_cost:
                cheapest_cost = cost
                cheapest_spawner = spawner
    return cheapest_spawner