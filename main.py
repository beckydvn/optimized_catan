from board import game_setup
from gui import draw
from constraints import Constraints
from gurobipy import GRB
import sys


def run(player_count: int, road_settlement_count: int, eval_mode: bool = False):
    """Runs the combinatorial Catan model with the given parameters. If eval_mode is True, the model will be optimized but not drawn, and the results will be returned for evaluation purposes."""
    if player_count < 3 or player_count > 6 or road_settlement_count < 2 or road_settlement_count > 6:
        raise ValueError("Invalid arguments. Please provide a player count (from 3 - 6) and a road/settlement count (from 2 - 6).")
    tiles = game_setup()
    constraint = Constraints(tiles, player_count, road_settlement_count)
    constraint.generate_constraints(evaluate_only=eval_mode)
    if not eval_mode and constraint.model.status == GRB.OPTIMAL:
        draw(tiles)
    return constraint.model

if __name__ == "__main__":
    # run as: python main 3 6 4 (or similar)
    player_count = int(sys.argv[1])
    road_settlement_count = int(sys.argv[2])
    
    run(player_count,road_settlement_count, eval_mode=False)