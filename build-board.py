from __future__ import annotations
from enum import Enum
import random
import tkinter as tk
import gurobipy as gp
from gurobipy import GRB

BOARD_LAYOUT = {0: 3, 1: 4, 2: 5, 3: 4, 4: 3}
HEX_HEIGHT = 50
HEX_SIZE = 100
MARGIN_X = 450
MARGIN_Y = 250
CIRCLE_RADIUS = HEX_SIZE // 2

def add_margin(point, row_idx):
    point = (point[0] + MARGIN_X, point[1] + MARGIN_Y)
    if row_idx  in [1, 3]:
        point = (point[0] - HEX_SIZE // 2, point[1])
    elif row_idx == 2:
        point = (point[0] - HEX_SIZE, point[1])
    return point

def get_hex_coords(row_idx, col_idx):
    hex_vertices = {
        VERTEX_ORIENTATION.N : (HEX_SIZE * col_idx - HEX_HEIGHT, HEX_SIZE * row_idx - HEX_HEIGHT),
        VERTEX_ORIENTATION.NE : (HEX_SIZE * col_idx, HEX_SIZE * row_idx),
        VERTEX_ORIENTATION.SW : (HEX_SIZE * col_idx - 2 * HEX_HEIGHT, HEX_SIZE * row_idx + HEX_HEIGHT),
        VERTEX_ORIENTATION.S : (HEX_SIZE * col_idx - HEX_HEIGHT, (HEX_SIZE * row_idx) + HEX_HEIGHT + HEX_HEIGHT),
        VERTEX_ORIENTATION.SE : (HEX_SIZE * col_idx, HEX_SIZE * row_idx + HEX_HEIGHT),
        VERTEX_ORIENTATION.NW : (HEX_SIZE * col_idx - 2 * HEX_HEIGHT, HEX_SIZE * row_idx)
    }

    for vo in VERTEX_ORIENTATION:
        hex_vertices[vo] = add_margin(hex_vertices[vo], row_idx)

    hex_edges = {
        EDGE_ORIENTATION.NE : [hex_vertices[VERTEX_ORIENTATION.N], hex_vertices[VERTEX_ORIENTATION.NE]],
        EDGE_ORIENTATION.E : [hex_vertices[VERTEX_ORIENTATION.NE], hex_vertices[VERTEX_ORIENTATION.SE]],
        EDGE_ORIENTATION.SE : [hex_vertices[VERTEX_ORIENTATION.SE], hex_vertices[VERTEX_ORIENTATION.S]],
        EDGE_ORIENTATION.SW : [hex_vertices[VERTEX_ORIENTATION.S], hex_vertices[VERTEX_ORIENTATION.SW]],
        EDGE_ORIENTATION.W : [hex_vertices[VERTEX_ORIENTATION.SW], hex_vertices[VERTEX_ORIENTATION.NW]],
        EDGE_ORIENTATION.NW : [hex_vertices[VERTEX_ORIENTATION.NW], hex_vertices[VERTEX_ORIENTATION.N]],
    }

    return hex_edges, hex_vertices

def board_GUI(tiles: list[list[Tile]]):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            # draw hexagon
            canvas.create_polygon(*get_hex_coords(row_idx, col_idx)[0].values(), outline='black', fill=get_type_colour(tile.type), width=2)
            
            # draw circle with dice text
            top_left_x = HEX_SIZE * col_idx - (HEX_HEIGHT // 2) - CIRCLE_RADIUS
            top_left_y = HEX_SIZE * row_idx + (HEX_HEIGHT) - CIRCLE_RADIUS
            top_left_x, top_left_y = add_margin((top_left_x, top_left_y), row_idx)
            bottom_right_x = HEX_SIZE * col_idx - (HEX_HEIGHT // 2)
            bottom_right_y = HEX_SIZE * row_idx + (HEX_HEIGHT)
            bottom_right_x, bottom_right_y = add_margin((bottom_right_x, bottom_right_y), row_idx)
            canvas.create_oval(top_left_x, top_left_y, bottom_right_x, bottom_right_y, fill="white", outline="black", width=2)
            canvas.create_text((top_left_x + bottom_right_x) / 2, (top_left_y + bottom_right_y) / 2, text=tile.dice, font=("Courier", 20, "bold"), fill="red" if tile.dice in [6, 8] else "black")
    # draw roads
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            hex_edges = get_hex_coords(row_idx, col_idx)[0]
            for o in EDGE_ORIENTATION:
                if tile.edges[o].road_placed:
                    canvas.create_polygon(hex_edges[o], outline=tile.edges[o].road_placed.owner.name.lower(), fill='white', width=10)
    # draw settlements
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            hex_vertices = get_hex_coords(row_idx, col_idx)[1]
            for o in EDGE_ORIENTATION:
                for vo in get_edge_to_vertex_orientation(o):
                    if tile.edges[o].vertices[vo].settlement_placed:
                        canvas.create_polygon(hex_vertices[vo], outline=tile.edges[o].vertices[vo].settlement_placed.owner.name.lower(), fill='white', width=15)

# Players and their colours
class Player(Enum):
    RED = 1
    BLUE = 2
    ORANGE = 3
    WHITE = 4

    def __str__(self):
        return self.name
    
def get_type_colour(tileType: TileType):
    return {
        TileType.WOOD: "#3A6B2A",
        TileType.BRICK: "#B5441E",
        TileType.SHEEP: "#7BBF3A",
        TileType.WHEAT: "#D4A843",
        TileType.ORE: "#8A8A7A",
        TileType.DESERT: "#C8A96A"
    }[tileType]

def get_edge_to_vertex_orientation(edge_orientation: EDGE_ORIENTATION):
    return {
        EDGE_ORIENTATION.W: {VERTEX_ORIENTATION.NW, VERTEX_ORIENTATION.SW},
        EDGE_ORIENTATION.NW: {VERTEX_ORIENTATION.N, VERTEX_ORIENTATION.NW},
        EDGE_ORIENTATION.NE: {VERTEX_ORIENTATION.N, VERTEX_ORIENTATION.NE},
        EDGE_ORIENTATION.E: {VERTEX_ORIENTATION.NE, VERTEX_ORIENTATION.SE},
        EDGE_ORIENTATION.SE: {VERTEX_ORIENTATION.SE, VERTEX_ORIENTATION.S},
        EDGE_ORIENTATION.SW: {VERTEX_ORIENTATION.SW, VERTEX_ORIENTATION.S}
    }[edge_orientation]

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
    def __init__(self, pos: tuple, orientation: VERTEX_ORIENTATION, edge_orientation: EDGE_ORIENTATION):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        self.edge_orientation = edge_orientation
        self.equal_to = set()
        self.ports = set()
        self.settlement_placed: Settlement | None = None

    def __str__(self):
        string = f"Vertex at ({self.row}, {self.col}, {self.orientation})"
        if self.settlement_placed:
            string += f" with settlement {self.settlement_placed}"
        return string

class Edge:
    def __init__(self, pos: tuple, orientation: EDGE_ORIENTATION):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        self.vertices = {}
        self.equal_to = set()
        self.road_placed: Road | None = None

    def __str__(self):
        string = f"Edge at ({self.row}, {self.col}, {self.orientation})"
        if self.road_placed:
            string += f" with road {self.road_placed}"
        return string

class Tile:
    def __init__(self, pos: tuple, type: TileType, dice: int, edges):
        self.row = pos[0]
        self.col = pos[1]
        self.type = type
        self.dice = dice
        self.edges = edges

    def __str__(self):
        return f"Tile at ({self.row}, {self.col}): {self.type} with dice {self.dice}"
    
def exists_in_board(row: int, col: int):
    if row in BOARD_LAYOUT and col < BOARD_LAYOUT[row] and col >= 0:
        return True
    return False

def get_orientation_idx(row: int, col: int, orientation: EDGE_ORIENTATION):
    new_row, new_col, new_orientation, new_vertex_map = None, None, None, {}
    if orientation == EDGE_ORIENTATION.W:
        if col > 0:
            new_row, new_col, new_orientation = (row, col - 1, EDGE_ORIENTATION.E)
            new_vertex_map[VERTEX_ORIENTATION.NW] = VERTEX_ORIENTATION.NE
            new_vertex_map[VERTEX_ORIENTATION.SW] = VERTEX_ORIENTATION.SE
    elif orientation == EDGE_ORIENTATION.E:
        if col < BOARD_LAYOUT[row] - 1:
            new_row, new_col, new_orientation = (row, col + 1, EDGE_ORIENTATION.W)
            new_vertex_map[VERTEX_ORIENTATION.NE] = VERTEX_ORIENTATION.NW
            new_vertex_map[VERTEX_ORIENTATION.SE] = VERTEX_ORIENTATION.SW
    elif orientation == EDGE_ORIENTATION.NW:
        if row > 0:
            new_row, new_col, new_orientation = (row - 1, col, EDGE_ORIENTATION.SE) if BOARD_LAYOUT[row - 1] > BOARD_LAYOUT[row] else (row - 1, col - 1, EDGE_ORIENTATION.SE)
            new_vertex_map[VERTEX_ORIENTATION.N] = VERTEX_ORIENTATION.SE
            new_vertex_map[VERTEX_ORIENTATION.NW] = VERTEX_ORIENTATION.S
    elif orientation == EDGE_ORIENTATION.NE:
        if row > 0:
            new_row, new_col, new_orientation = (row - 1, col + 1, EDGE_ORIENTATION.SW) if BOARD_LAYOUT[row - 1] > BOARD_LAYOUT[row] else (row - 1, col, EDGE_ORIENTATION.SW)
            new_vertex_map[VERTEX_ORIENTATION.N] = VERTEX_ORIENTATION.SW
            new_vertex_map[VERTEX_ORIENTATION.NE] = VERTEX_ORIENTATION.S
    elif orientation == EDGE_ORIENTATION.SW:
        if row < len(BOARD_LAYOUT) - 1:
            new_row, new_col, new_orientation = (row + 1, col, EDGE_ORIENTATION.NE) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col - 1, EDGE_ORIENTATION.NE)
            new_vertex_map[VERTEX_ORIENTATION.S] = VERTEX_ORIENTATION.NE
            new_vertex_map[VERTEX_ORIENTATION.SW] = VERTEX_ORIENTATION.N
    elif orientation == EDGE_ORIENTATION.SE:
        if row < len(BOARD_LAYOUT) - 1:
            new_row, new_col, new_orientation = (row + 1, col + 1, EDGE_ORIENTATION.NW) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col , EDGE_ORIENTATION.NW)
            new_vertex_map[VERTEX_ORIENTATION.S] = VERTEX_ORIENTATION.NW
            new_vertex_map[VERTEX_ORIENTATION.SE] = VERTEX_ORIENTATION.N

    if new_row is not None:
        if exists_in_board(new_row, new_col):
            return (new_row, new_col, new_orientation, new_vertex_map)
        return None
    print()

def add_board_connections(tiles: list[list[Tile]]):
    last_row_idx = len(BOARD_LAYOUT) - 1
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in EDGE_ORIENTATION:
                result = get_orientation_idx(row_idx, col_idx, o)
                if result:
                    new_row, new_col, new_orientation, new_vertex_map = result
                    tile.edges[o].equal_to.add(tiles[new_row][new_col].edges[new_orientation])
                    for vo in get_edge_to_vertex_orientation(o):
                        tile.edges[o].vertices[vo].equal_to.add(tiles[new_row][new_col].edges[new_orientation].vertices[new_vertex_map[vo]])

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

            vertices = {}
            edges = {}
            for o in EDGE_ORIENTATION:
                edges[o] = Edge(pos, o)
                edges[o].vertices = {vo: Vertex(pos, vo, o) for vo in get_edge_to_vertex_orientation(o)}

            row.append(Tile(pos, type, dice, edges))
        all_tiles.append(row)
    add_board_connections(all_tiles)
    return (all_tiles)   

def general_constraints(tiles: list[list[Tile]]):
    # every player places 2 settlements and 2 roads
    # CONSTRAINT 1: every player places 2 settlements and 2 roads
    model = gp.Model(f"Catan Constraints")
    settlements = {}
    roads = {}

    for player in Player:
        # start by creating binary variables for every possible settlement and road placement
        settlements[player] = model.addVars([(row_idx, col_idx, o, vo) for row_idx in BOARD_LAYOUT for col_idx in range(BOARD_LAYOUT[row_idx]) for o in EDGE_ORIENTATION for vo in get_edge_to_vertex_orientation(o)], vtype=GRB.BINARY, name="Settlement")
        roads[player] = model.addVars([(row_idx, col_idx, o) for row_idx in BOARD_LAYOUT for col_idx in range(BOARD_LAYOUT[row_idx]) for o in EDGE_ORIENTATION], vtype=GRB.BINARY, name="Road")
        model.addConstr(settlements[player].sum() == 2, name=f"{player}_settlements")
        model.addConstr(roads[player].sum() == 2, name=f"{player}_roads")

    # CONSTRAINT 2: settlements can't be placed on the same vertex and roads can't be placed on the same edge
    # we use the "equal_to" sets we created to add constraints that the sum of all settlements on vertices in the same "equal_to" set is at most 1, and similarly for roads and edges
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in EDGE_ORIENTATION:
                edge = tile.edges[o]
                for player in Player:
                    # sum the current road binary var with the road binary vars for all equivalent edges
                    all_road_var = roads[player][row_idx, col_idx, o] + gp.quicksum(roads[p][equal_edge.row, equal_edge.col, equal_edge.orientation] for equal_edge in edge.equal_to for p in Player)
                    # only one of these can be true
                    model.addConstr(all_road_var <= 1, name=f"{player}_road_{row_idx}_{col_idx}_{o}")
                    for vo in get_edge_to_vertex_orientation(o):
                        # sum the current settlement binary var with the settlement binary vars for all equivalent vertices
                        all_settlement_var = settlements[player][row_idx, col_idx, o, vo] + gp.quicksum(settlements[p][equal_vertex.row, equal_vertex.col, equal_vertex.edge_orientation, equal_vertex.orientation] for equal_vertex in edge.vertices[vo].equal_to for p in Player)
                        # only one of these can be true                        
                        model.addConstr(all_settlement_var <= 1, name=f"{player}_settlement_{row_idx}_{col_idx}_{o}_{vo}")


    # CONSTRAINT 2: all settlements must be at least distance 2 from each other (no adjacent settlements)
    # iterate through the grid vertices
    # add implication constraint that if a settlement is placed at a vertex, no settlement is on the vertex it is connected to (forces them to be 2 away or more)
    # for row_idx in BOARD_LAYOUT:
    #     for col_idx in range(BOARD_LAYOUT[row_idx]):
    #         for o in EDGE_ORIENTATION:
    #             for vo in get_edge_to_vertex_orientation(o):
    #                 for player in Player:
    #                     for settlement in settlements[player].keys():
    #                         model.addGenConstrIndicator(settlement, True, y == 1)


    model.optimize()
    assert model.status == GRB.OPTIMAL

    for player in Player:
        for key, var in settlements[player].items():
            if var.x > 0.5:  # binary var is 1
                tiles[key[0]][key[1]].edges[key[2]].vertices[key[3]].settlement_placed = Settlement(player)
                print(f"Player {player} settlement at {key}")
        for key, var in roads[player].items():
            if var.x > 0.5:
                tiles[key[0]][key[1]].edges[key[2]].road_placed = Road(player)
                print(f"Player {player} road at {key}")

if __name__ == "__main__":
    tiles = game_setup()

    # print vertex connections
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in EDGE_ORIENTATION:
                print(f"Tile ({row_idx}, {col_idx}) edge {o} equal to {[f'({t.row}, {t.col}, {t.orientation})' for t in tile.edges[o].equal_to]}")
                for vo in get_edge_to_vertex_orientation(o):
                    print(f"Tile ({row_idx}, {col_idx}) edge {o} vertex {vo} equal to {[f'({v.row}, {v.col}, {v.orientation})' for v in tile.edges[o].vertices[vo].equal_to]}")

    general_constraints(tiles)

    root = tk.Tk()
    root.title("Catan Board")
    
    canvas = tk.Canvas(root, width = 1000, height = 1000, bg="#3A9EC4")
    canvas.pack()
    board_GUI(tiles)
    root.mainloop()