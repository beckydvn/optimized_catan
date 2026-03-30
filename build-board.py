from __future__ import annotations
from enum import Enum
import random

BOARD_LAYOUT = {1: 3, 2: 4, 3: 5, 4: 4, 5: 3}
# MIN_SPACE = " "
# MARGIN = 50

# def print_board(all_tiles: list[list[Tile]]):
#     # iterate through the board configuration
#     for row in BOARD_LAYOUT:
#         num_cols = BOARD_LAYOUT[row]
#         if row == 1:
#             top_str = f"/{MIN_SPACE}\\{MIN_SPACE*2}" * num_cols
#             # center the top string
#             top_str = top_str.center(MARGIN)
#             print(top_str)
#         mid_str = f"|{MIN_SPACE*3}" * (num_cols + 1)
#         mid_str = mid_str.center(MARGIN)
#         print(mid_str)
#         bot_str = f"\\{MIN_SPACE}/{MIN_SPACE*2}" * num_cols
#         bot_str = bot_str.center(MARGIN)
#         print(bot_str)
        

# Players and their colours
class Player(Enum):
    RED = 1
    BLUE = 2
    ORANGE = 3

    def __str__(self):
        return self.name

# TileType types
class TileType(Enum):
    WOOD = 1
    BRICK = 2
    SHEEP = 3
    WHEAT = 4
    ORE = 5
    DESERT = 6

    def __str__(self):
        return self.name

class ORIENTATION(Enum):
    N = 1
    NW = 2
    SW = 3
    S = 4
    SE = 5
    NE = 6

class Port:
    def __init__(self, pos: tuple, type: TileType):
        self.x = pos[0]
        self.y = pos[1]
        self.orientation = ORIENTATION
        self.type = type

class Property:
    def __init__(self, pos: tuple, owner: Player):
        self.x = pos[0]
        self.y = pos[1]
        self.owner = owner

class Road(Property):
    def __init__(self, pos: tuple, owner: Player):
        super().__init__(pos, owner)

class City(Property):
    def __init__(self, pos: tuple, owner: Player):
        super().__init__(pos, owner)

class Vertex:
    def __init__(self, pos: tuple, connected_to: list[Vertex], ports_connected_to: list[Port]):
        self.x = pos[0]
        self.y = pos[1]
        self.connected_to = connected_to
        self.ports_connected_to = ports_connected_to
        self.property_placed: Property | None = None

class Edge:
    def __init__(self, pos: tuple, connected_to: list[Edge]):
        self.x = pos[0]
        self.y = pos[1]
        self.connected_to = connected_to
        self.road_placed: Road | None = None

class Tile:
    def __init__(self, pos: tuple, type: TileType, dice: int, vertices: list[Vertex], edges: list[Edge], connected_to: list[Tile]):
        self.x = pos[0]
        self.y = pos[1]
        self.type = type
        self.dice = dice
        self.vertices = vertices
        self.edges = edges
        self.connected_to = connected_to
    
def game_setup():
    number_pieces = [
        2, 
        3, 3, 
        4, 4, 
        5, 5, 
        6, 6,
        8, 8, 
        9, 9, 
        10, 10, 
        11, 11, 
        12
    ]
    tiles = [
        TileType.DESERT,
        TileType.WHEAT, TileType.WHEAT, TileType.WHEAT, TileType.WHEAT,
        TileType.BRICK, TileType.BRICK, TileType.BRICK,
        TileType.ORE, TileType.ORE, TileType.ORE,
        TileType.SHEEP, TileType.SHEEP, TileType.SHEEP, TileType.SHEEP,
        TileType.WOOD, TileType.WOOD, TileType.WOOD, TileType.WOOD
    ]
    # shuffle the number pieces and tile types to generate a random board
    random.shuffle(number_pieces)
    random.shuffle(tiles)

    all_tiles = []

    for row_idx in BOARD_LAYOUT:
        row = []
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            pos = (row_idx, col_idx)
            type = tiles.pop()
            dice = number_pieces.pop() if type != TileType.DESERT else 0

            vertices = {}
            edges = {}
            for o in ORIENTATION:
                vertices[o] = Vertex(pos, set(), set())
                edges[o] = Edge(pos, set())

            row.append(Tile(pos, type, dice, vertices, edges, set()))


            print(f"Tile at ({row_idx}, {col_idx}): {type} with dice {dice}")
        all_tiles.append(row)
    
    return all_tiles


if __name__ == "__main__":
    all_tiles = game_setup()
