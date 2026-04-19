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
                        canvas.create_polygon(hex_vertices[vo], outline=tile.edges[o].vertices[vo].settlement_placed.owner.name.lower(), fill='white', width=25)

# Players and their colours
class Player(Enum):
    RED = 1
    # BLUE = 2
    # ORANGE = 3
    # WHITE = 4

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
    def __init__(self, pos: tuple, orientation: VERTEX_ORIENTATION, edge: Edge):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        self.edge = edge
        self.equal_to = set()
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
        self.vertices = {}
        self.equal_to = set()
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
    def __init__(self, pos: tuple, type: TileType, dice: int, edges):
        self.row = pos[0]
        self.col = pos[1]
        self.type = type
        self.dice = dice
        self.edges = edges

    def __str__(self):
        return f"Tile at ({self.row}, {self.col}): {self.type} with dice {self.dice}"
    
    def __hash__(self):
        return hash(str(self))
    
def exists_in_board(row: int, col: int):
    if row in BOARD_LAYOUT and col < BOARD_LAYOUT[row] and col >= 0:
        return True
    return False

def get_orientation_idx(row: int, col: int, orientation: EDGE_ORIENTATION):
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
    
# def get_edges_w_vtx(vo: Vertex, tile: Tile):
#     edges_w_vtx = {tile.edges[v_edge] for v_edge in tile.edges if vo in tile.edges[v_edge].vertices}
#     equal_edges = [(equal_edge, ) for v_edge in edges_w_vtx for equal_edge in v_edge.equal_to]
#     edges_w_vtx.update(equal_edges)
#     return edges_w_vtx

def add_board_connections(tiles: list[list[Tile]]):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in EDGE_ORIENTATION:
                result = get_orientation_idx(row_idx, col_idx, o)
                if result:
                    new_row, new_col, new_orientation, vertex_map = result
                    tile.edges[o].equal_to.add(tiles[new_row][new_col].edges[new_orientation])
                    for vo in get_edge_to_vertex_orientation(o):
                        # add the vertex equality relative to the new edge
                        tile.edges[o].vertices[vo].equal_to.add(tiles[new_row][new_col].edges[new_orientation].vertices[vertex_map[vo]])
                
                # also get the other edges in this tile that have this vertex
                for vo in get_edge_to_vertex_orientation(o):
                    edges_w_vtx = {tile.edges[v_edge] for v_edge in tile.edges if vo in tile.edges[v_edge].vertices}
                    for e in edges_w_vtx:
                        tile.edges[o].vertices[vo].equal_to.add(tiles[e.row][e.col].edges[e.orientation].vertices[vo])                    

def get_adjacency(adjacency_order, idx):
    return {adjacency_order[(idx - 1) % len(adjacency_order)], adjacency_order[(idx + 1) % len(adjacency_order)]}

def get_vertex_adjacencies(vo: VERTEX_ORIENTATION):
    adjacency_order = [VERTEX_ORIENTATION.N, VERTEX_ORIENTATION.NE, VERTEX_ORIENTATION.SE, VERTEX_ORIENTATION.S, VERTEX_ORIENTATION.SW, VERTEX_ORIENTATION.NW]
    idx = adjacency_order.index(vo)
    return get_adjacency(adjacency_order, idx)

def add_vertex_adjacencies(tiles: list[list[Tile]]):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in EDGE_ORIENTATION:
                this_edge = tile.edges[o]
                for vo in get_edge_to_vertex_orientation(o):
                    this_edge.vertices[vo].adjacencies = set()
                    adj_vo = get_vertex_adjacencies(vo)
                    for av in adj_vo:
                        # find the adjacent edge with this vertex
                        for adj_e in tile.edges[o].adjacencies:
                            if av in adj_e.vertices:
                                this_edge.vertices[vo].adjacencies.add((adj_e, av))

def get_edge_adjacencies(o: EDGE_ORIENTATION):
    adjacency_order = [EDGE_ORIENTATION.NW, EDGE_ORIENTATION.NE, EDGE_ORIENTATION.E, EDGE_ORIENTATION.SE, EDGE_ORIENTATION.SW, EDGE_ORIENTATION.W]
    idx = adjacency_order.index(o)
    return get_adjacency(adjacency_order, idx)

def add_edge_adjacencies(tiles: list[list[Tile]]):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in EDGE_ORIENTATION:
                # edges directly adjacent
                tile.edges[o].adjacencies = {tile.edges[adj_o] for adj_o in get_edge_adjacencies(o)} 
                for equal_edge in tile.edges[o].equal_to:
                    # edges adjacent in the other tile (get this by getting the "equal" edge and getting the edges adjacent to those ones)
                    tile.edges[o].adjacencies.update({tiles[equal_edge.row][equal_edge.col].edges[adj_o] for adj_o in get_edge_adjacencies(equal_edge.orientation)})

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
            edges = {}
            for o in EDGE_ORIENTATION:
                edges[o] = Edge(pos, o)
                edges[o].vertices = {vo: Vertex(pos, vo, edges[o]) for vo in get_edge_to_vertex_orientation(o)}
            row.append(Tile(pos, type, dice, edges))
        all_tiles.append(row)
    add_board_connections(all_tiles)
    add_edge_adjacencies(all_tiles)
    add_vertex_adjacencies(all_tiles)
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
                # for player in Player:
                # sum the current road binary var with the road binary vars for all equivalent edges
                all_road_var = gp.quicksum(roads[p][row_idx, col_idx, o] for p in Player) + gp.quicksum(roads[p][equal_edge.row, equal_edge.col, equal_edge.orientation] for equal_edge in edge.equal_to for p in Player)
                # only one of these can be true
                model.addConstr(all_road_var <= 1, name=f"{player}_road_{row_idx}_{col_idx}_{o}")
                for vo in get_edge_to_vertex_orientation(o):
                    # sum the current settlement binary var with the settlement binary vars for all equivalent vertices
                    all_settlement_var = gp.quicksum(settlements[p][row_idx, col_idx, o, vo] for p in Player) + gp.quicksum(settlements[p][equal_vertex.edge.row, equal_vertex.edge.col, equal_vertex.edge.orientation, equal_vertex.orientation] for equal_vertex in edge.vertices[vo].equal_to for p in Player)
                    # only one of these can be true                        
                    model.addConstr(all_settlement_var <= 1, name=f"{player}_settlement_{row_idx}_{col_idx}_{o}_{vo}")

    # CONSTRAINT 3: all settlements must be at least distance 2 from each other (no adjacent settlements)
    # iterate through the grid vertices
    # add implication constraint that if a settlement is placed at a vertex, no settlement is on any vertices it is connected to (forces them to be 2 away or more)
    # for row_idx in BOARD_LAYOUT:
    #     for col_idx in range(BOARD_LAYOUT[row_idx]):
    #         tile = tiles[row_idx][col_idx]
    #         for o in EDGE_ORIENTATION:
    #             for vo in get_edge_to_vertex_orientation(o):
    #                 for player in Player:
    #                     model.addGenConstrIndicator(settlements[player][row_idx, col_idx, o, vo], True, gp.quicksum(settlements[p][adj_e.row, adj_e.col, adj_e.orientation, adj_v] for (adj_e, adj_v) in tile.edges[o].vertices[vo].adjacencies for p in Player) == 0)

    # CONSTRAINT 4: all settlements must be connected to a road also owned by that player
    # for row_idx in BOARD_LAYOUT:
    #     for col_idx in range(BOARD_LAYOUT[row_idx]):
    #         tile = tiles[row_idx][col_idx]
    #         for o in EDGE_ORIENTATION:
    #             for vo in get_edge_to_vertex_orientation(o):
    #                 for player in Player:
    #                     possible_edges = [v_eq.edge for v_eq in tile.edges[o].vertices[vo].equal_to]
    #                     model.addGenConstrIndicator(settlements[player][row_idx, col_idx, o, vo], True, gp.quicksum(roads[player][edge.row, edge.col, edge.orientation] for edge in possible_edges) >= 1)
    # count how many variables are in the model
    print(f"Number of settlement vars: {sum(len(settlements[p]) for p in Player)}")
    print(f"Number of road vars: {sum(len(roads[p]) for p in Player)}")
    print(f"Number of constraints: {model.numConstrs}")
    model.optimize()

    if model.status == GRB.INFEASIBLE:
        print("Model is infeasible, computing IIS...")
        model.computeIIS()
        model.write("infeasible.ilp")  # writes the conflicting constraints to a file
        
        # print the conflicting constraints directly
        for c in model.getConstrs():
            if c.IISConstr:
                print(f"Conflicting constraint: {c.constrName}")
    # assert model.status == GRB.OPTIMAL

    for player in Player:
        for key, var in settlements[player].items():
            if var.x == 1:  # binary var is 1
                tiles[key[0]][key[1]].edges[key[2]].vertices[key[3]].settlement_placed = Settlement(player)
                print(f"Player {player} settlement at {key}")
        for key, var in roads[player].items():
            if var.x == 1:
                tiles[key[0]][key[1]].edges[key[2]].road_placed = Road(player)
                print(f"Player {player} road at {key}")

if __name__ == "__main__":
    tiles = game_setup()

    # print vertex connections
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in EDGE_ORIENTATION:
                # print(f"Edge ({row_idx}, {col_idx}, {o}) is adjacent to {[str(adj) for adj in tile.edges[o].adjacencies]}")
                # print(f"Tile ({row_idx}, {col_idx}) edge {o} equal to {[f'({t.row}, {t.col}, {t.orientation})' for t in tile.edges[o].equal_to]}")
                for vo in get_edge_to_vertex_orientation(o):
                    # print(f"Vertex ({row_idx}, {col_idx}, {vo}) is adjacent to {[(str(adj[0]), str(adj[1])) for adj in tile.edges[o].vertices[vo].adjacencies]}")
                    print(f"\nTile ({row_idx}, {col_idx}) edge {o}, vertex {vo} equal to:") 
                    for v in tile.edges[o].vertices[vo].equal_to:
                        print(f"({v.row}, {v.col}, edge {v.edge.orientation}, vertex {v.orientation})")
            print()
        print()
    general_constraints(tiles)

    root = tk.Tk()
    root.title("Catan Board")
    
    canvas = tk.Canvas(root, width = 1000, height = 1000, bg="#3A9EC4")
    canvas.pack()
    board_GUI(tiles)
    root.mainloop()