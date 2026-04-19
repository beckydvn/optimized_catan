from board import game_setup
from gui import draw
from constraints import general_constraints

if __name__ == "__main__":
    tiles = game_setup()
    general_constraints(tiles)
    draw(tiles)