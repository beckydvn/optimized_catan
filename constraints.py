from board import BOARD_LAYOUT, Tile, EDGE_ORIENTATION, VERTEX_ORIENTATION, Player, Settlement, Road
from gurobipy import Model, GRB
import gurobipy as gp

def two_settlements_two_roads_constraint(settlements: dict, roads: dict, model: Model):
    # every player places exactly 2 roads and 2 settlements
    for player in Player:
        model.addConstr(settlements[player].sum() == 2)
        model.addConstr(roads[player].sum() == 2)

def no_overlaps_constraint(tiles: list[list[Tile]], settlements: dict, roads: dict, model: Model):
    # settlements can't be placed on the same vertex and roads can't be placed on the same edge
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            for o in EDGE_ORIENTATION:
                model.addConstr(gp.quicksum(roads[p][id(tiles[row_idx][col_idx].edges[o])] for p in Player)  <= 1)
            for vo in VERTEX_ORIENTATION:
                model.addConstr(gp.quicksum(settlements[p][id(tiles[row_idx][col_idx].vertices[vo])] for p in Player) <= 1)

def road_connected_settlement_constraint(tiles: list[list[Tile]], settlements: dict, roads: dict, model: Model):
    # all settlements must be connected to a road also owned by that player
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            for vo in VERTEX_ORIENTATION:
                for p in Player:
                    model.addGenConstrIndicator(settlements[p][id(tiles[row_idx][col_idx].vertices[vo])], True, gp.quicksum(roads[p][id(adj_e)] for adj_e in tiles[row_idx][col_idx].vertices[vo].adjacent_edges) >= 1)

def generate_constraints(tiles: list[list[Tile]]):
    model = gp.Model(f"Catan Constraints")
    canonical_edges = {}
    canonical_vertices = {}

    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            for o in EDGE_ORIENTATION:
                edge = tiles[row_idx][col_idx].edges[o]
                canonical_edges[id(edge)] = edge  # duplicate ids just overwrite, no error
            for vo in VERTEX_ORIENTATION:
                vertex = tiles[row_idx][col_idx].vertices[vo]
                canonical_vertices[id(vertex)] = vertex
    roads = {}
    settlements = {}

    # now pass only unique keys to gurobi
    for player in Player:
        roads[player] = model.addVars(canonical_edges.keys(), vtype=GRB.BINARY, name="road")
        settlements[player] = model.addVars(canonical_vertices.keys(), vtype=GRB.BINARY, name="settlement")

    two_settlements_two_roads_constraint(settlements, roads, model)
    no_overlaps_constraint(tiles, settlements, roads, model)
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
                canonical_vertices[key].settlement_placed = Settlement(player)
                print(f"Player {player} settlement at {key}")
        for key, var in roads[player].items():
            if var.x == 1:
                canonical_edges[key].road_placed = Road(player)
                print(f"Player {player} road at {key}")
    