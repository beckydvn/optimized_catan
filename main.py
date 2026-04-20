from board import game_setup
from gui import draw
from constraints import Constraints
import sys


def run(player_count: int, road_count: int, settlement_count: int, eval_mode: bool = False):
    """Runs the combinatorial Catan model with the given parameters. If eval_mode is True, the model will be optimized but not drawn, and the results will be returned for evaluation purposes."""
    if player_count < 3 or player_count > 6 or road_count < 2 or road_count > 6 or settlement_count < 2 or settlement_count > 4:
        raise ValueError("Invalid arguments. Please provide a player count (from 3 - 6), a road count (from 2 - 6), and a settlement count (from 2 - 4).")
    tiles = game_setup()
    constraint = Constraints(tiles, player_count, road_count, settlement_count)
    constraint.generate_constraints(evaluate_only=eval_mode)
    if not eval_mode:
        draw(tiles)
    return constraint.model

if __name__ == "__main__":
    # run as: python main 3 6 4 (or similar)
    player_count = int(sys.argv[1])
    road_count = int(sys.argv[2])
    settlement_count = int(sys.argv[3])
    
    run(player_count, road_count, settlement_count, eval_mode=False)