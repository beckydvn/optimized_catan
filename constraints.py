from board import BOARD_LAYOUT, Tile, EDGE_ORIENTATION, VERTEX_ORIENTATION, Player, Settlement, Road
from gurobipy import Model, GRB
import gurobipy as gp

# def vertices_to_edge(edge_orientation: EDGE_ORIENTATION):
#     return {
#         {VERTEX_ORIENTATION.NW, VERTEX_ORIENTATION.SW}: EDGE_ORIENTATION.W,
#         EDGE_ORIENTATION.NW: {VERTEX_ORIENTATION.N, VERTEX_ORIENTATION.NW},
#         EDGE_ORIENTATION.NE: {VERTEX_ORIENTATION.N, VERTEX_ORIENTATION.NE},
#         EDGE_ORIENTATION.E: {VERTEX_ORIENTATION.NE, VERTEX_ORIENTATION.SE},
#         EDGE_ORIENTATION.SE: {VERTEX_ORIENTATION.SE, VERTEX_ORIENTATION.S},
#         EDGE_ORIENTATION.SW: {VERTEX_ORIENTATION.SW, VERTEX_ORIENTATION.S}
#     }[edge_orientation]

def two_settlements_two_roads_constraint(settlements: dict, roads: dict, model: Model):
    # every player places exactly 2 roads and 2 settlements
    for player in Player:
        # start by creating binary variables for every possible settlement and road placement
        roads[player] = model.addVars([(row_idx, col_idx, o) for row_idx in BOARD_LAYOUT for col_idx in range(BOARD_LAYOUT[row_idx]) for o in EDGE_ORIENTATION], vtype=GRB.BINARY, name="Road")
        settlements[player] = model.addVars([(row_idx, col_idx, vo) for row_idx in BOARD_LAYOUT for col_idx in range(BOARD_LAYOUT[row_idx]) for vo in VERTEX_ORIENTATION], vtype=GRB.BINARY, name="Settlement")
        model.addConstr(settlements[player].sum() == 2)
        model.addConstr(roads[player].sum() == 2)

def no_overlaps_constraint(settlements: dict, roads: dict, model: Model):
    # settlements can't be placed on the same vertex and roads can't be placed on the same edge
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            for o in EDGE_ORIENTATION:
                model.addConstr(gp.quicksum(roads[p][row_idx, col_idx, o] for p in Player)  <= 1)
            for vo in VERTEX_ORIENTATION:
                model.addConstr(gp.quicksum(settlements[p][row_idx, col_idx, vo] for p in Player) <= 1)

def road_connected_settlement_constraint(tiles: list[list[Tile]], settlements: dict, roads: dict, model: Model):
    # all settlements must be connected to a road also owned by that player
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            for vo in VERTEX_ORIENTATION:
                for p in Player:
                    model.addGenConstrIndicator(settlements[p][row_idx, col_idx, vo], True, gp.quicksum(roads[p][adj_e.row, adj_e.col, adj_e.orientation] for adj_e in tiles[row_idx][col_idx].vertices[vo].adjacent_edges) >= 1)

def generate_constraints(tiles: list[list[Tile]]):
    model = gp.Model(f"Catan Constraints")
    settlements = {}
    roads = {}
    two_settlements_two_roads_constraint(settlements, roads, model)
    no_overlaps_constraint(settlements, roads, model)
    road_connected_settlement_constraint(tiles, settlements, roads, model)

    model.optimize()
    if model.status == GRB.INFEASIBLE:
        print("Model is infeasible, computing IIS...")
        model.computeIIS()
        model.write("infeasible.ilp")  # writes the conflicting constraints to a file
        
        # print the conflicting constraints directly
        for c in model.getConstrs():
            if c.IISConstr:
                print(f"Conflicting constraint: {c.constrName}")

    assert model.status == GRB.OPTIMAL

    for player in Player:
        for key, var in settlements[player].items():
            if var.x == 1:  # binary var is 1
                tiles[key[0]][key[1]].vertices[key[2]].settlement_placed = Settlement(player)
                print(f"Player {player} settlement at {key}")
        for key, var in roads[player].items():
            if var.x == 1:
                tiles[key[0]][key[1]].edges[key[2]].road_placed = Road(player)
                print(f"Player {player} road at {key}")
    