from __future__ import annotations
from enum import Enum
import random
import tkinter as tk

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

def get_hex_edges(row_idx, col_idx):
    # calculate hexagon position
    hex_edges = {
                ORIENTATION.NE : [
                    (HEX_SIZE * col_idx, HEX_SIZE * row_idx),
                    (HEX_SIZE * col_idx - HEX_HEIGHT, HEX_SIZE * row_idx - HEX_HEIGHT)],
                ORIENTATION.NW : [(HEX_SIZE * col_idx - HEX_HEIGHT, HEX_SIZE * row_idx - HEX_HEIGHT),
                    (HEX_SIZE * col_idx - 2 * HEX_HEIGHT, HEX_SIZE * row_idx)],
                ORIENTATION.E : [(HEX_SIZE * col_idx - 2 * HEX_HEIGHT, HEX_SIZE * row_idx),
                    (HEX_SIZE * col_idx - 2 * HEX_HEIGHT, HEX_SIZE * row_idx + HEX_HEIGHT)],
                ORIENTATION.SW : [(HEX_SIZE * col_idx - 2 * HEX_HEIGHT, HEX_SIZE * row_idx + HEX_HEIGHT),
                    (HEX_SIZE * col_idx - HEX_HEIGHT, (HEX_SIZE * row_idx) + HEX_HEIGHT + HEX_HEIGHT)],
                ORIENTATION.SE : [(HEX_SIZE * col_idx - HEX_HEIGHT, (HEX_SIZE * row_idx) + HEX_HEIGHT + HEX_HEIGHT),
                    (HEX_SIZE * col_idx, HEX_SIZE * row_idx + HEX_HEIGHT)],
                ORIENTATION.W : [(HEX_SIZE * col_idx, HEX_SIZE * row_idx),
                    (HEX_SIZE * col_idx, HEX_SIZE * row_idx + HEX_HEIGHT)]
            }
    # add margins
    for o in ORIENTATION:
        for j in range(2):
            hex_edges[o][j] = add_margin(hex_edges[o][j], row_idx)

    return hex_edges

def board_GUI(tiles: list[list[Tile]]):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            # draw hexagon
            canvas.create_polygon(*get_hex_edges(row_idx, col_idx).values(), outline='black', fill=get_type_colour(tile.type), width=2)
            
            # draw circle with dice text
            top_left_x = HEX_SIZE * col_idx - (HEX_HEIGHT // 2) - CIRCLE_RADIUS
            top_left_y = HEX_SIZE * row_idx + (HEX_HEIGHT) - CIRCLE_RADIUS
            top_left_x, top_left_y = add_margin((top_left_x, top_left_y), row_idx)
            bottom_right_x = HEX_SIZE * col_idx - (HEX_HEIGHT // 2)
            bottom_right_y = HEX_SIZE * row_idx + (HEX_HEIGHT)
            bottom_right_x, bottom_right_y = add_margin((bottom_right_x, bottom_right_y), row_idx)
            canvas.create_oval(top_left_x, top_left_y, bottom_right_x, bottom_right_y, fill="white", outline="black", width=2)
            canvas.create_text((top_left_x + bottom_right_x) / 2, (top_left_y + bottom_right_y) / 2, text=tile.dice, font=("Courier", 20, "bold"), fill="red" if tile.dice in [6, 8] else "black")

    tiles[0][0].edges[ORIENTATION.W].road_placed = Road((0, 0), Player.RED)
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in ORIENTATION:
                if tile.edges[o].road_placed:
                    canvas.create_polygon(get_hex_edges(row_idx, col_idx)[o], outline=tile.edges[o].road_placed.owner.name.lower(), fill='white', width=20)

# Players and their colours
class Player(Enum):
    RED = 1
    BLUE = 2
    ORANGE = 3

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
    W = 1
    NW = 2
    SW = 3
    E = 4
    SE = 5
    NE = 6

    def __str__(self):
        return self.name

class Port:
    def __init__(self, pos: tuple, type: TileType):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = ORIENTATION
        self.type = type

class Property:
    def __init__(self, pos: tuple, owner: Player):
        self.row = pos[0]
        self.col = pos[1]
        self.owner = owner

class Road(Property):
    def __init__(self, pos: tuple, owner: Player):
        super().__init__(pos, owner)

class Settlement(Property):
    def __init__(self, pos: tuple, owner: Player):
        super().__init__(pos, owner)

class Vertex:
    def __init__(self, pos: tuple, orientation: ORIENTATION):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        self.connected_to = set()
        self.ports_connected_to = set()
        self.property_placed: Property | None = None

    def __str__(self):
        string = f"Vertex at ({self.row}, {self.col}, {self.orientation})"
        if self.property_placed:
            string += f" with property {self.property_placed}"
        return string

class Edge:
    def __init__(self, pos: tuple, orientation: ORIENTATION):
        self.row = pos[0]
        self.col = pos[1]
        self.orientation = orientation
        self.connected_to = set()
        self.road_placed: Road | None = None

    def __str__(self):
        string = f"Edge at ({self.row}, {self.col}, {self.orientation})"
        if self.road_placed:
            string += f" with road {self.road_placed}"
        return string

class Tile:
    def __init__(self, pos: tuple, type: TileType, dice: int, vertices: list[Vertex], edges: list[Edge]):
        self.row = pos[0]
        self.col = pos[1]
        self.type = type
        self.dice = dice
        self.vertices = vertices
        self.edges = edges
        self.connected_to = set()

    def __str__(self):
        return f"Tile at ({self.row}, {self.col}): {self.type} with dice {self.dice}"
    
def exists_in_board(row: int, col: int):
    if row in BOARD_LAYOUT and col < BOARD_LAYOUT[row] and col >= 0:
        return True
    return False

def get_orientation_idx(row: int, col: int, orientation: ORIENTATION):
    new_row, new_col, new_orientation = None, None, None
    if orientation == ORIENTATION.W:
        if col > 0:
            new_row, new_col, new_orientation = (row, col - 1, ORIENTATION.E)
    elif orientation == ORIENTATION.E:
        if col < BOARD_LAYOUT[row] - 1:
            new_row, new_col, new_orientation = (row, col + 1, ORIENTATION.W)
    elif orientation == ORIENTATION.NW:
        if row > 0:
            new_row, new_col, new_orientation = (row - 1, col, ORIENTATION.SE) if BOARD_LAYOUT[row - 1] > BOARD_LAYOUT[row] else (row - 1, col - 1, ORIENTATION.SE)
    elif orientation == ORIENTATION.NE:
        if row > 0:
            new_row, new_col, new_orientation = (row - 1, col + 1, ORIENTATION.SW) if BOARD_LAYOUT[row - 1] > BOARD_LAYOUT[row] else (row - 1, col, ORIENTATION.SW)
    elif orientation == ORIENTATION.SW:
        if row < len(BOARD_LAYOUT) - 1:
            new_row, new_col, new_orientation = (row + 1, col, ORIENTATION.NE) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col - 1, ORIENTATION.NE)
    elif orientation == ORIENTATION.SE:
        if row < len(BOARD_LAYOUT) - 1:
            new_row, new_col, new_orientation = (row + 1, col + 1, ORIENTATION.NW) if BOARD_LAYOUT[row + 1] > BOARD_LAYOUT[row] else (row + 1, col , ORIENTATION.NW)

    if new_row is not None:
        if exists_in_board(new_row, new_col):
            return (new_row, new_col, new_orientation)
        return None

def add_board_connections(tiles: list[list[Tile]]):
    last_row_idx = len(BOARD_LAYOUT) - 1
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            for o in ORIENTATION:
                idx = get_orientation_idx(row_idx, col_idx, o)
                if idx:
                    tile.connected_to.add(tiles[idx[0]][idx[1]])
                    tile.edges[o].connected_to.add(tiles[idx[0]][idx[1]].edges[idx[2]])
                    tile.vertices[o].connected_to.add(tiles[idx[0]][idx[1]].vertices[idx[2]])

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
                vertices[o] = Vertex(pos, o)
                edges[o] = Edge(pos, o)

            row.append(Tile(pos, type, dice, vertices, edges))
        all_tiles.append(row)
    add_board_connections(all_tiles)
    return (all_tiles)

if __name__ == "__main__":
    tiles = game_setup()

    root = tk.Tk()
    root.title("Catan Board")
    
    canvas = tk.Canvas(root, width = 1000, height = 1000, bg="#3A9EC4")
    canvas.pack()

    board_GUI(tiles)

    root.mainloop()