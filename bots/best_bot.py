from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.built_explorer = False  # Track if exploration building is placed
        self.farms_built = 0  # Track farm count
        pass
    
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
            possible = rc.get_building_placeable_map
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
            
        for unit in units:
            for enem in unitsEnem:
                if rc.can_unit_attack(unit.id,enem.id):
                    rc.unit_attack_unit(unit.id,enem.id)

        for unit in units:
            for build in enemBuildings:
                if rc.can_unit_attack_building(unit.id,build.id):
                    rc.unit_attack_building(unit.id,build.id)
                