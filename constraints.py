from board import BOARD_LAYOUT, Tile, TileType, EDGE_ORIENTATION, VERTEX_ORIENTATION, Player, Settlement, Road
from gurobipy import Model, GRB
import gurobipy as gp

def general_constraints(tiles: list[list[Tile]]):
    # every player places 2 settlements and 2 roads
    # CONSTRAINT 1: every player places 2 settlements and 2 roads
    model = gp.Model(f"Catan Constraints")
    settlements = {}
    roads = {}

    for player in Player:
        # start by creating binary variables for every possible settlement and road placement
        settlements[player] = model.addVars([(row_idx, col_idx, vo) for row_idx in BOARD_LAYOUT for col_idx in range(BOARD_LAYOUT[row_idx]) for vo in VERTEX_ORIENTATION], vtype=GRB.BINARY, name="Settlement")
        roads[player] = model.addVars([(row_idx, col_idx, o) for row_idx in BOARD_LAYOUT for col_idx in range(BOARD_LAYOUT[row_idx]) for o in EDGE_ORIENTATION], vtype=GRB.BINARY, name="Road")
        model.addConstr(settlements[player].sum() == 2, name=f"{player}_settlements")
        model.addConstr(roads[player].sum() == 2, name=f"{player}_roads")


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
                tiles[key[0]][key[1]].vertices[key[2]].settlement_placed = Settlement(player)
                print(f"Player {player} settlement at {key}")
        for key, var in roads[player].items():
            if var.x == 1:
                tiles[key[0]][key[1]].edges[key[2]].road_placed = Road(player)
                print(f"Player {player} road at {key}")
    