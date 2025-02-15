from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building
from collections import deque

class BotPlayer(Player):

    def attack_units(rc: RobotController, unit_list):
        good_guys = []
        bad_guys = []
        for units in unit_list:
            if rc.get_team_of_unit(units.id) == rc.get_enemy_team():
                bad_guys.append(units)
            else: 
                good_guys.append(units)
        for guy in good_guys:
            for badg in bad_guys:
                if(rc.can_unit_attack_building(guy.id, badg.id)):
                    rc.unit_attack_unit(guy.id, badg.id)

    def defend_farms(rc: RobotController, x):
        num_units = 0
        for u in x:
            if rc.get_team_of_unit(u.id) == rc.get_enemy_team():
                num_units+=1
        buildings = rc.get_buildings(rc.get_ally_team)
        for i in buildings:
            if isinstance(i, BuildingType.FARM_1):
                rc.spawn_unit(UnitType.Knight, i.id)
        

    def __init__(self, map: Map):
        self.built_explorer = False  # Track if exploration building is placed
        self.farms_built = 0  # Track farm count
        pass
    
    def path_to_location(self, rc : RobotController, starting_x, starting_y, end_x, end_y):
        possibilities = rc.get_unit_placeable_map()
        DIRECTIONS = {
            (0, 1): Direction.UP,
            (0, -1): Direction.DOWN,
            (1, 0): Direction.RIGHT,
            (-1, 0): Direction.LEFT,
            (1, 1): Direction.UP_RIGHT,
            (-1, 1): Direction.UP_LEFT,
            (1, -1): Direction.DOWN_RIGHT,
            (-1, -1): Direction.DOWN_LEFT
        }

        queue = deque([(starting_x, starting_y, [])])
        
        visited = set()
        visited.add((starting_x, starting_y))

        while queue:
            x, y, path = queue.popleft()
            if (x, y) == (end_x, end_y):
                return path

            for (dx, dy), direction in DIRECTIONS.items():
                new_x, new_y = x + dx, y + dy

                if (0 <= new_x < len(possibilities) and 
                    0 <= new_y < len(possibilities[0]) and
                    possibilities[new_x][new_y] and  
                    (new_x, new_y) not in visited): 

                    queue.append((new_x, new_y, path + [direction]))
                    visited.add((new_x, new_y))
                    
        return []

    def move_unit(self, rc, unit_id, directions):
        for direction in directions:
            if rc.can_move_unit_in_direction(unit_id, direction): 
                rc.move_unit_in_direction(unit_id, direction)  
            else:
                break

    def play_turn(self, rc: RobotController):
        turn = rc.get_turn()
        balance = rc.get_balance(rc.get_ally_team())
        buildings = rc.get_buildings(rc.get_ally_team())
        
            

        # Build farms early for economy
        if self.farms_built < 2 and balance >= 30:
            for x in range(rc.get_map().width):
                for y in range(rc.get_map().height):
                    if rc.can_build_building(BuildingType.FARM_1, x, y):
                        rc.build_building(BuildingType.FARM_1, x, y)
                        self.farms_built += 1
                        return

        # Build an explorer building to train troops
        if not self.built_explorer and balance >= 100:
            possible = rc.get_building_placeable_map()
            dist = 1000
            place_x = -1
            place_y = -1
            for i in range(len(possible)):
                for j in range(len(possible[i])):
                    if possible[i][j] == True:
                        castle = buildings[0]
                        cur_dist = rc.get_chebyshev_distance(castle.x,castle.y,i,j)
                        if cur_dist < dist:
                            place_x = i
                            place_y = j
                            dist = cur_dist
            if place_x != -1:
                rc.build_building(BuildingType.EXPLORER_BUILDING, place_x,place_y)
            self.built_explorer = True
     
                

        # Train an Explorer for gold gathering
        if self.built_explorer and balance >= 10:
            for building in buildings:
                if rc.can_spawn_unit(UnitType.EXPLORER, building.id):
                    rc.spawn_unit(UnitType.EXPLORER, building.id)
                    return

        # Spawn and train warriors for attack
        if balance >= 2:
            for building in buildings:
                if rc.can_spawn_unit(UnitType.WARRIOR, building.id):
                    rc.spawn_unit(UnitType.WARRIOR, building.id)
                    return

        # Move units towards enemy castles
        units = rc.get_units(rc.get_ally_team())
        unitsEnem = rc.get_units(rc.get_enemy_team())
        enemBuildings = rc.get_buildings(rc.get_enemy_team())
        for unit in units:
            possible_moves = rc.unit_possible_move_directions(unit.id)
            if possible_moves:
                rc.move_unit_in_direction(unit.id, possible_moves[0])
                return
        #Attack Enemies   
        for unit in units:
            for enem in unitsEnem:
                if rc.can_unit_attack(unit.id,enem.id):
                    rc.unit_attack_unit(unit.id,enem.id)

        for unit in units:
            for build in enemBuildings:
                if rc.can_unit_attack_building(unit.id,build.id):
                    rc.unit_attack_building(unit.id,build.id)
                