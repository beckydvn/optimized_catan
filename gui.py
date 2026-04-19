from board import Tile, TileType, PortType, EDGE_ORIENTATION, VERTEX_ORIENTATION
from config import *
import tkinter as tk

def get_type_colour(tileType: TileType):
    return {
        TileType.WOOD: "#3A6B2A",
        TileType.BRICK: "#B5441E",
        TileType.SHEEP: "#7BBF3A",
        TileType.WHEAT: "#D4A843",
        TileType.ORE: "#8A8A7A",
        TileType.DESERT: "#F4DEB1"
    }[tileType]

def get_port_colour(portType: PortType):
    return {
        PortType.WOOD: "#0C2405",
        PortType.BRICK: "#711500",
        PortType.SHEEP: "#5DC000",
        PortType.WHEAT: "#9A6C00",
        PortType.ORE: "#38382C",
        PortType.MISC: "#FFFFFF"
    }[portType]

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

def board_GUI(tiles: list[list[Tile]], canvas):
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
    # draw ports
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            tile = tiles[row_idx][col_idx]
            hex_vertices = get_hex_coords(row_idx, col_idx)[1]
            for vo in VERTEX_ORIENTATION:
                if tile.vertices[vo].port:    
                    canvas.create_polygon(hex_vertices[vo], outline=get_port_colour(tile.vertices[vo].port.type), fill='white', width=35)
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
            for vo in VERTEX_ORIENTATION:
                if tile.vertices[vo].settlement_placed:
                    canvas.create_polygon(hex_vertices[vo], outline=tile.vertices[vo].settlement_placed.owner.name.lower(), fill='white', width=25)
                

def draw(tiles: list[list[Tile]]):
    root = tk.Tk()
    root.title("Catan Board")
    
    canvas = tk.Canvas(root, width = 1000, height = 1000, bg="#3A9EC4")
    canvas.pack()
    board_GUI(tiles, canvas)
    root.mainloop()