from board import game_setup
from gui import draw
from constraints import generate_constraints

if __name__ == "__main__":
    tiles = game_setup()
    generate_constraints(tiles)
    draw(tiles)