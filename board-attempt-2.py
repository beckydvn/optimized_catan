from __future__ import annotations
from enum import Enum
import random

BOARD_LAYOUT = {0: 3, 1: 4, 2: 5, 3: 4, 4: 3}

# Players and their colours
class Player(Enum):
    RED = 1
    # BLUE = 2
    # ORANGE = 3
    # WHITE = 4

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

class EDGE_ORIENTATION(Enum):
    W = 1
    NW = 2
    SW = 3
    E = 4
    SE = 5
    NE = 6

    def __str__(self):
        return self.name
    
class VERTEX_ORIENTATION(Enum):
    N = 1
    NW = 2
    SW = 3
    S = 4
    SE = 5
    NE = 6

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

class EDGE_ORIENTATION(Enum):
    W = 1
    NW = 2
    SW = 3
    E = 4
    SE = 5
    NE = 6

    def __str__(self):
        return self.name
    
class VERTEX_ORIENTATION(Enum):
    N = 1
    NW = 2
    SW = 3
    S = 4
    SE = 5
    NE = 6

    def __str__(self):
        return self.name

class Port:
    def __init__(self, pos: tuple, type: TileType):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = VERTEX_ORIENTATION
        self.type = type

class Road:
    def __init__(self, owner: Player):
        self.owner = owner
    
    def __str__(self):
        return f"Road owned by {self.owner}"

class Settlement:
    def __init__(self, owner: Player):
        self.owner = owner

    def __str__(self):
        return f"Settlement owned by {self.owner}"

class Vertex:
    def __init__(self, pos: tuple, orientation: VERTEX_ORIENTATION):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        self.ports = set()
        self.adjacencies = set()
        self.settlement_placed: Settlement | None = None

    def __str__(self):
        string = f"Vertex at ({self.row}, {self.col}, {self.orientation})"
        if self.settlement_placed:
            string += f" with settlement {self.settlement_placed}"
        return string
    
    def __hash__(self):
        return hash(str(self))

class Edge:
    def __init__(self, pos: tuple, orientation: EDGE_ORIENTATION):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        # self.vertices = {}
        self.adjacencies = set()
        self.road_placed: Road | None = None

    def __str__(self):
        string = f"Edge at ({self.row}, {self.col}, {self.orientation})"
        if self.road_placed:
            string += f" with road {self.road_placed}"
        return string
    
    def __hash__(self):
        return hash(str(self))

class Tile:
    def __init__(self, pos: tuple, type: TileType, dice: int):
        self.row = pos[0]
        self.col = pos[1]
        self.type = type
        self.dice = dice
        self.edges = {}
        self.vertices = {}

    def __str__(self):
        return f"Tile at ({self.row}, {self.col}): {self.type} with dice {self.dice}"
    
    def __hash__(self):
        return hash(str(self))
    
def get_edge_to_vertex_orientation(edge_orientation: EDGE_ORIENTATION):
    return {
        EDGE_ORIENTATION.W: {VERTEX_ORIENTATION.NW, VERTEX_ORIENTATION.SW},
        EDGE_ORIENTATION.NW: {VERTEX_ORIENTATION.N, VERTEX_ORIENTATION.NW},
        EDGE_ORIENTATION.NE: {VERTEX_ORIENTATION.N, VERTEX_ORIENTATION.NE},
        EDGE_ORIENTATION.E: {VERTEX_ORIENTATION.NE, VERTEX_ORIENTATION.SE},
        EDGE_ORIENTATION.SE: {VERTEX_ORIENTATION.SE, VERTEX_ORIENTATION.S},
        EDGE_ORIENTATION.SW: {VERTEX_ORIENTATION.SW, VERTEX_ORIENTATION.S}
    }[edge_orientation]

# def create_vertices(row: int, col: int, orientation: VERTEX_ORIENTATION):
#     new_row, new_col, new_orientation = None, None, None
#     if orientation == VERTEX_ORIENTATION.N:
#         new_row, new_col, new_orientation = (row, col, VERTEX_ORIENTATION.N)
#     elif orientation == VERTEX_ORIENTATION.NW:
#         new_row, new_col, new_orientation = (row, col, VERTEX_ORIENTATION.NW)
#     elif orientation == VERTEX_ORIENTATION.NE:
#         new_row, new_col, new_orientation = (row, col, VERTEX_ORIENTATION.NE)
#     elif orientation == VERTEX_ORIENTATION.SW:
#         new_row, new_col, new_orientation = (row, col, VERTEX_ORIENTATION.SW)
#     elif orientation == VERTEX_ORIENTATION.S:
#         if row < len(BOARD_LAYOUT) - 1:
#             new_row, new_col, new_orientation = (row + 1, col, VERTEX_ORIENTATION.NE) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col - 1, VERTEX_ORIENTATION.NE)
#         else:
#             new_row, new_col, new_orientation = (row, col, VERTEX_ORIENTATION.S)
#     elif orientation == VERTEX_ORIENTATION.SE:
#         if row < len(BOARD_LAYOUT) - 1:
#             new_row, new_col, new_orientation = (row + 1, col + 1, VERTEX_ORIENTATION.N) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col, VERTEX_ORIENTATION.N)
#         else:
#             new_row, new_col, new_orientation = (row, col, VERTEX_ORIENTATION.SE)
#     return (new_row, new_col, new_orientation)

# def create_edges(row: int, col: int, orientation: EDGE_ORIENTATION):
#     new_row, new_col, new_orientation = None, None, None
#     if orientation == EDGE_ORIENTATION.W:
#         new_row, new_col, new_orientation = (row, col, EDGE_ORIENTATION.W)
#     elif orientation == EDGE_ORIENTATION.NW:
#         new_row, new_col, new_orientation = (row, col, EDGE_ORIENTATION.NW)
#     elif orientation == EDGE_ORIENTATION.NE:
#         new_row, new_col, new_orientation = (row, col, EDGE_ORIENTATION.NE)
#     elif orientation == EDGE_ORIENTATION.E:
#         if col < BOARD_LAYOUT[row] - 1:
#             new_row, new_col, new_orientation = (row, col + 1, EDGE_ORIENTATION.W)
#         else:
#             new_row, new_col, new_orientation = (row, col, EDGE_ORIENTATION.E)
#     elif orientation == EDGE_ORIENTATION.SW:
#         if row < len(BOARD_LAYOUT) - 1:
#             new_row, new_col, new_orientation = (row + 1, col, EDGE_ORIENTATION.NE) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col - 1, EDGE_ORIENTATION.NE)
#         else:
#             new_row, new_col, new_orientation = (row, col, EDGE_ORIENTATION.SW)
#     elif orientation == EDGE_ORIENTATION.SE:
#         if row < len(BOARD_LAYOUT) - 1:
#             new_row, new_col, new_orientation = (row + 1, col + 1, EDGE_ORIENTATION.NW) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col , EDGE_ORIENTATION.NW)
#         else:
#             new_row, new_col, new_orientation = (row, col, EDGE_ORIENTATION.SE)

#     return (new_row, new_col, new_orientation)

def exists_in_board(row: int, col: int):
    if row in BOARD_LAYOUT and col < BOARD_LAYOUT[row] and col >= 0:
        return True
    return False

def create_canonical_edges(tiles):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]

            # reuse from left neighbor (same row)
            if col_idx > 0:
                left = tiles[row_idx][col_idx - 1]
                tile.edges[EDGE_ORIENTATION.W] = left.edges[EDGE_ORIENTATION.E]

            # reuse from upper neighbor
            if row_idx > 0:
                expanding = BOARD_LAYOUT[row_idx] > BOARD_LAYOUT[row_idx - 1]  # rows 1, 2
                shrinking = BOARD_LAYOUT[row_idx] < BOARD_LAYOUT[row_idx - 1]  # rows 3, 4

                if expanding:
                    # upper row is shorter, tiles shift right
                    # col_idx 0 has no NW neighbor, col_idx 1+ maps to col_idx-1 above
                    if col_idx > 0 and exists_in_board(row_idx - 1, col_idx - 1):
                        above = tiles[row_idx - 1][col_idx - 1]
                        tile.edges[EDGE_ORIENTATION.NW] = above.edges[EDGE_ORIENTATION.SW]
                    if exists_in_board(row_idx - 1, col_idx - 1) and col_idx > 0:
                        tile.edges[EDGE_ORIENTATION.NE] = above.edges[EDGE_ORIENTATION.SE]
                elif shrinking:
                    # upper row is longer, tiles shift left
                    if exists_in_board(row_idx - 1, col_idx + 1):
                        above_nw = tiles[row_idx - 1][col_idx]
                        above_ne = tiles[row_idx - 1][col_idx + 1]
                        tile.edges[EDGE_ORIENTATION.NW] = above_nw.edges[EDGE_ORIENTATION.SW]
                        tile.edges[EDGE_ORIENTATION.NE] = above_ne.edges[EDGE_ORIENTATION.SE]
                else:
                    # same length row (middle row 2->2 doesn't happen here but just in case)
                    if exists_in_board(row_idx - 1, col_idx):
                        above = tiles[row_idx - 1][col_idx]
                        tile.edges[EDGE_ORIENTATION.NW] = above.edges[EDGE_ORIENTATION.SW]
                        tile.edges[EDGE_ORIENTATION.NE] = above.edges[EDGE_ORIENTATION.SE]

            # create new edges for any not yet assigned
            for o in EDGE_ORIENTATION:
                if o not in tile.edges or tile.edges[o] is None:
                    tile.edges[o] = Edge((row_idx, col_idx), o)

def create_canonical_vertices(tiles):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]

            # reuse from left neighbor (same row)
            if col_idx > 0:
                left = tiles[row_idx][col_idx - 1]
                tile.vertices[VERTEX_ORIENTATION.NW] = left.vertices[VERTEX_ORIENTATION.NE]
                tile.vertices[VERTEX_ORIENTATION.SW] = left.vertices[VERTEX_ORIENTATION.SE]

            # reuse from upper neighbor
            if row_idx > 0:
                expanding = BOARD_LAYOUT[row_idx] > BOARD_LAYOUT[row_idx - 1]
                shrinking = BOARD_LAYOUT[row_idx] < BOARD_LAYOUT[row_idx - 1]

                if expanding:
                    if col_idx > 0 and exists_in_board(row_idx - 1, col_idx - 1):
                        above = tiles[row_idx - 1][col_idx - 1]
                        tile.vertices[VERTEX_ORIENTATION.NW] = above.vertices[VERTEX_ORIENTATION.SW]
                        tile.vertices[VERTEX_ORIENTATION.N]  = above.vertices[VERTEX_ORIENTATION.S]
                    if exists_in_board(row_idx - 1, col_idx):
                        above_ne = tiles[row_idx - 1][col_idx]
                        tile.vertices[VERTEX_ORIENTATION.NE] = above_ne.vertices[VERTEX_ORIENTATION.SE]
                elif shrinking:
                    if exists_in_board(row_idx - 1, col_idx):
                        above_nw = tiles[row_idx - 1][col_idx]
                        tile.vertices[VERTEX_ORIENTATION.NW] = above_nw.vertices[VERTEX_ORIENTATION.SW]
                        tile.vertices[VERTEX_ORIENTATION.N]  = above_nw.vertices[VERTEX_ORIENTATION.S]
                    if exists_in_board(row_idx - 1, col_idx + 1):
                        above_ne = tiles[row_idx - 1][col_idx + 1]
                        tile.vertices[VERTEX_ORIENTATION.NE] = above_ne.vertices[VERTEX_ORIENTATION.SE]
                else:
                    if exists_in_board(row_idx - 1, col_idx):
                        above = tiles[row_idx - 1][col_idx]
                        tile.vertices[VERTEX_ORIENTATION.NW] = above.vertices[VERTEX_ORIENTATION.SW]
                        tile.vertices[VERTEX_ORIENTATION.N]  = above.vertices[VERTEX_ORIENTATION.S]
                        tile.vertices[VERTEX_ORIENTATION.NE] = above.vertices[VERTEX_ORIENTATION.SE]

            # create new vertices for any not yet assigned
            for vo in VERTEX_ORIENTATION:
                if vo not in tile.vertices or tile.vertices[vo] is None:
                    tile.vertices[vo] = Vertex((row_idx, col_idx), vo)

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
            dice = number_pieces.pop() if type != TileType.DESERT else 7
            # edges = {}
            # for o in EDGE_ORIENTATION:
            #     edge_row, edge_col, edge_o = create_canonical_edges(row_idx, col_idx, o)
            #     edges[o] = Edge((edge_row, edge_col), edge_o)
            #     for vo in get_edge_to_vertex_orientation(o):
            #         v_row, v_col, vo = create_canonical_vertices(row_idx, col_idx, vo)
            #         edges[o].vertices[vo] = Vertex((v_row, v_col), vo)
            row.append(Tile(pos, type, dice))
        all_tiles.append(row)

    create_canonical_vertices(all_tiles)
    create_canonical_edges(all_tiles)

    # verify no duplicates
    all_edges = set()
    all_vertices = set()

    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = all_tiles[row_idx][col_idx]
            for o in EDGE_ORIENTATION:
                all_edges.add(id(tile.edges[o]))
                for vo in VERTEX_ORIENTATION:
                    all_vertices.add(id(tile.vertices[vo]))

    print(f"Unique edges: {len(all_edges)}")      # expect 72
    print(f"Unique vertices: {len(all_vertices)}") # expect 54

    # add_board_connections(all_tiles)
    # add_edge_adjacencies(all_tiles)
    # add_vertex_adjacencies(all_tiles)
    return (all_tiles) 

if __name__ == "__main__":
    tiles = game_setup()