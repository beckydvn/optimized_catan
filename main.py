from board import game_setup
from gui import draw
from constraints import Constraints
import sys

# run as: python board.py 4

if __name__ == "__main__":
    player_count = int(sys.argv[1])
    road_count = int(sys.argv[2])
    settlement_count = int(sys.argv[3])
    if player_count < 3 or player_count > 6 or road_count < 2 or road_count > 6 or settlement_count < 2 or settlement_count > 4:
        raise ValueError("Invalid arguments. Please provide a player count (from 3 - 6), a road count (from 2 - 6), and a settlement count (from 2 - 4).")
    tiles = game_setup()
    constraint = Constraints(tiles, player_count, road_count, settlement_count)
    constraint.generate_constraints()
    draw(tiles)