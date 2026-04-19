from __future__ import annotations
from enum import Enum
import random
import gurobipy as gp
from gurobipy import GRB
from config import BOARD_LAYOUT

# Players and their colours
class Player(Enum):
    RED = 1
    BLUE = 2
    PURPLE = 3

    def __repr__(self):
        return self.name

class PortType(Enum):
    WOOD = 1
    BRICK = 2
    SHEEP = 3
    WHEAT = 4
    ORE = 5
    MISC = 6

    def __repr__(self):
        return self.name

class TileType(Enum):
    WOOD = 1
    BRICK = 2
    SHEEP = 3
    WHEAT = 4
    ORE = 5
    DESERT = 6

    def __repr__(self):
        return self.name

class EDGE_ORIENTATION(Enum):
    W = 1
    NW = 2
    SW = 3
    E = 4
    SE = 5
    NE = 6

    def __repr__(self):
        return self.name
    
class VERTEX_ORIENTATION(Enum):
    N = 1
    NW = 2
    SW = 3
    S = 4
    SE = 5
    NE = 6

    def __repr__(self):
        return self.name

class Port:
    def __init__(self, type: PortType):
        self.type = type

class Road:
    def __init__(self, owner: Player):
        self.owner = owner
    
    def __repr__(self):
        return f"Road owned by {self.owner}"

class Settlement:
    def __init__(self, owner: Player):
        self.owner = owner

    def __repr__(self):
        return f"Settlement owned by {self.owner}"

class Vertex:
    def __init__(self, pos: tuple, orientation: VERTEX_ORIENTATION, tile: Tile):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        self.port = None
        self.adjacent_vertices = set()
        self.adjacent_edges = set()
        self.settlement_placed: Settlement | None = None
        self.tile = tile

    def __repr__(self):
        string = f"Vertex at ({self.row}, {self.col}, {self.orientation})"
        if self.settlement_placed:
            string += f" with settlement {self.settlement_placed}"
        return string
    
    def __hash__(self):
        return hash(str(self))

class Edge:
    def __init__(self, pos: tuple, orientation: EDGE_ORIENTATION, tile: Tile):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        # self.vertices = {}
        self.adjacent_edges = set()
        self.road_placed: Road | None = None
        self.tile = tile

    def __repr__(self):
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

    def __repr__(self):
        return f"Tile at ({self.row}, {self.col}): {self.type} with dice {self.dice}"
    
    def __hash__(self):
        return hash(str(self))

def exists_in_board(row: int, col: int):
    if row in BOARD_LAYOUT and col < BOARD_LAYOUT[row] and col >= 0:
        return True
    return False

def get_equivalent(row: int, col: int, orientation: EDGE_ORIENTATION):
    new_row, new_col, new_orientation, vertex_map = None, None, None, {}
    if orientation == EDGE_ORIENTATION.W:
        if col > 0:
            new_row, new_col, new_orientation = (row, col - 1, EDGE_ORIENTATION.E)
            vertex_map[VERTEX_ORIENTATION.NW] = VERTEX_ORIENTATION.NE
            vertex_map[VERTEX_ORIENTATION.SW] = VERTEX_ORIENTATION.SE
    elif orientation == EDGE_ORIENTATION.E:
        if col < BOARD_LAYOUT[row] - 1:
            new_row, new_col, new_orientation = (row, col + 1, EDGE_ORIENTATION.W)
            vertex_map[VERTEX_ORIENTATION.NE] = VERTEX_ORIENTATION.NW
            vertex_map[VERTEX_ORIENTATION.SE] = VERTEX_ORIENTATION.SW
    elif orientation == EDGE_ORIENTATION.NW:
        if row > 0:
            new_row, new_col, new_orientation = (row - 1, col, EDGE_ORIENTATION.SE) if BOARD_LAYOUT[row - 1] > BOARD_LAYOUT[row] else (row - 1, col - 1, EDGE_ORIENTATION.SE)
            vertex_map[VERTEX_ORIENTATION.N] = VERTEX_ORIENTATION.SE
            vertex_map[VERTEX_ORIENTATION.NW] = VERTEX_ORIENTATION.S
    elif orientation == EDGE_ORIENTATION.NE:
        if row > 0:
            new_row, new_col, new_orientation = (row - 1, col + 1, EDGE_ORIENTATION.SW) if BOARD_LAYOUT[row - 1] > BOARD_LAYOUT[row] else (row - 1, col, EDGE_ORIENTATION.SW)
            vertex_map[VERTEX_ORIENTATION.N] = VERTEX_ORIENTATION.SW
            vertex_map[VERTEX_ORIENTATION.NE] = VERTEX_ORIENTATION.S
    elif orientation == EDGE_ORIENTATION.SW:
        if row < len(BOARD_LAYOUT) - 1:
            new_row, new_col, new_orientation = (row + 1, col, EDGE_ORIENTATION.NE) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col - 1, EDGE_ORIENTATION.NE)
            vertex_map[VERTEX_ORIENTATION.S] = VERTEX_ORIENTATION.NE
            vertex_map[VERTEX_ORIENTATION.SW] = VERTEX_ORIENTATION.N
    elif orientation == EDGE_ORIENTATION.SE:
        if row < len(BOARD_LAYOUT) - 1:
            new_row, new_col, new_orientation = (row + 1, col + 1, EDGE_ORIENTATION.NW) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col , EDGE_ORIENTATION.NW)
            vertex_map[VERTEX_ORIENTATION.S] = VERTEX_ORIENTATION.NW
            vertex_map[VERTEX_ORIENTATION.SE] = VERTEX_ORIENTATION.N

    if new_row is not None:
        if exists_in_board(new_row, new_col):
            return (new_row, new_col, new_orientation, vertex_map)
        return None

def create_canonical_edges(tiles):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]

            for o in EDGE_ORIENTATION:
                if o not in tile.edges or tile.edges[o] is None:
                    # check if this edge already exists from a neighbor's perspective
                    neighbor = get_equivalent(row_idx, col_idx, o)
                    if neighbor is not None:
                        n_row, n_col, n_orientation, _ = neighbor
                        # reuse the neighbor's edge object if it already exists
                        if n_orientation in tiles[n_row][n_col].edges and tiles[n_row][n_col].edges[n_orientation] is not None:
                            tile.edges[o] = tiles[n_row][n_col].edges[n_orientation]
                        else:
                            tile.edges[o] = Edge((row_idx, col_idx), o, tile)
                    else:
                        tile.edges[o] = Edge((row_idx, col_idx), o, tile)

def create_canonical_vertices(tiles):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for vo in VERTEX_ORIENTATION:
                if vo not in tile.vertices or tile.vertices[vo] is None:
                    # search through all edges to find if this vertex already exists on a neighbor
                    found = False
                    for o in EDGE_ORIENTATION:
                        neighbor = get_equivalent(row_idx, col_idx, o)
                        if neighbor is None:
                            continue
                        n_row, n_col, _, vertex_map = neighbor
                        if vo in vertex_map:
                            mapped_vo = vertex_map[vo]
                            neighbor_tile = tiles[n_row][n_col]
                            if mapped_vo in neighbor_tile.vertices and neighbor_tile.vertices[mapped_vo] is not None:
                                tile.vertices[vo] = neighbor_tile.vertices[mapped_vo]
                                found = True
                                break
                    if not found:
                        tile.vertices[vo] = Vertex((row_idx, col_idx), vo, tile)

def add_ports(tiles):
    tiles[0][0].vertices[VERTEX_ORIENTATION.N].port = Port(PortType.MISC)
    tiles[0][0].vertices[VERTEX_ORIENTATION.NW].port = Port(PortType.MISC)

    tiles[0][1].vertices[VERTEX_ORIENTATION.N].port = Port(PortType.WHEAT)
    tiles[0][1].vertices[VERTEX_ORIENTATION.NE].port = Port(PortType.WHEAT)

    tiles[1][0].vertices[VERTEX_ORIENTATION.NW].port = Port(PortType.WOOD)
    tiles[1][0].vertices[VERTEX_ORIENTATION.SW].port = Port(PortType.WOOD)

    tiles[1][3].vertices[VERTEX_ORIENTATION.N].port = Port(PortType.ORE)
    tiles[1][3].vertices[VERTEX_ORIENTATION.NE].port = Port(PortType.ORE)

    tiles[2][4].vertices[VERTEX_ORIENTATION.NE].port = Port(PortType.MISC)
    tiles[2][4].vertices[VERTEX_ORIENTATION.SE].port = Port(PortType.MISC)

    tiles[3][0].vertices[VERTEX_ORIENTATION.NW].port = Port(PortType.BRICK)
    tiles[3][0].vertices[VERTEX_ORIENTATION.SW].port = Port(PortType.BRICK)

    tiles[3][3].vertices[VERTEX_ORIENTATION.SE].port = Port(PortType.SHEEP)
    tiles[3][3].vertices[VERTEX_ORIENTATION.S].port = Port(PortType.SHEEP)

    tiles[4][0].vertices[VERTEX_ORIENTATION.SW].port = Port(PortType.MISC)
    tiles[4][0].vertices[VERTEX_ORIENTATION.S].port = Port(PortType.MISC)

    tiles[4][1].vertices[VERTEX_ORIENTATION.S].port = Port(PortType.MISC)
    tiles[4][1].vertices[VERTEX_ORIENTATION.SE].port = Port(PortType.MISC)

def get_adjacency(adjacency_order, idx):
    return {adjacency_order[(idx - 1) % len(adjacency_order)], adjacency_order[(idx + 1) % len(adjacency_order)]}

def get_vertex_edge_adjacencies(vo: VERTEX_ORIENTATION):
    # maps each vertex to the 2 edges that touch it on this tile
    adjacency_map = {
        VERTEX_ORIENTATION.N:  [EDGE_ORIENTATION.NW, EDGE_ORIENTATION.NE],
        VERTEX_ORIENTATION.NE: [EDGE_ORIENTATION.NE, EDGE_ORIENTATION.E],
        VERTEX_ORIENTATION.SE: [EDGE_ORIENTATION.E,  EDGE_ORIENTATION.SE],
        VERTEX_ORIENTATION.S:  [EDGE_ORIENTATION.SE, EDGE_ORIENTATION.SW],
        VERTEX_ORIENTATION.SW: [EDGE_ORIENTATION.SW, EDGE_ORIENTATION.W],
        VERTEX_ORIENTATION.NW: [EDGE_ORIENTATION.W,  EDGE_ORIENTATION.NW],
    }
    return adjacency_map[vo]

def get_vertex_adjacencies(vo: VERTEX_ORIENTATION):
    adjacency_order = [VERTEX_ORIENTATION.N, VERTEX_ORIENTATION.NE, VERTEX_ORIENTATION.SE, VERTEX_ORIENTATION.S, VERTEX_ORIENTATION.SW, VERTEX_ORIENTATION.NW]
    idx = adjacency_order.index(vo)
    return get_adjacency(adjacency_order, idx)

def get_edge_adjacencies(o: EDGE_ORIENTATION):
    adjacency_order = [EDGE_ORIENTATION.NW, EDGE_ORIENTATION.NE, EDGE_ORIENTATION.E, EDGE_ORIENTATION.SE, EDGE_ORIENTATION.SW, EDGE_ORIENTATION.W]
    idx = adjacency_order.index(o)
    return get_adjacency(adjacency_order, idx)

def build_adjacencies(tiles):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]

            for o in EDGE_ORIENTATION:
                edge = tile.edges[o]
                # add adjacent edges from this tile's perspective
                for adj_o in get_edge_adjacencies(o):
                    edge.adjacent_edges.add(tile.edges[adj_o])

            for vo in VERTEX_ORIENTATION:
                vertex = tile.vertices[vo]
                # add adjacent vertices from this tile's perspective
                for adj_vo in get_vertex_adjacencies(vo):
                    vertex.adjacent_vertices.add(tile.vertices[adj_vo])
                # add edge adjacencies
                for adj_o in get_vertex_edge_adjacencies(vo):
                    vertex.adjacent_edges.add(tile.edges[adj_o])

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
            row.append(Tile(pos, type, dice))
        all_tiles.append(row)

    create_canonical_vertices(all_tiles)
    add_ports(all_tiles)
    create_canonical_edges(all_tiles)
    
    build_adjacencies(all_tiles)

    return (all_tiles) 


# if __name__ == "__main__":
#     tiles = game_setup()
#     # general_constraints(tiles)
    