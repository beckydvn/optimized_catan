from board import BOARD_LAYOUT, Tile, EDGE_ORIENTATION, VERTEX_ORIENTATION, Player, Settlement, Road, TileType
from gurobipy import Model, GRB
import gurobipy as gp

def probability_score(value: int):
    return {
        7: 0,
        2: 1,
        12: 1,
        3: 2,
        11: 2,
        4: 3,
        10: 3,
        5: 4,
        9: 4,
        6: 5,
        8: 5
    }[value]

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

def settlement_distance_constraint(tiles: list[list[Tile]], settlements: dict, model: Model):
    for row_idx in BOARD_LAYOUT:
        for col_idx in range(BOARD_LAYOUT[row_idx]):
            for vo in VERTEX_ORIENTATION:
                for player in Player:
                    model.addGenConstrIndicator(settlements[player][id(tiles[row_idx][col_idx].vertices[vo])], True, gp.quicksum(settlements[p][id(tiles[adj_v.row][adj_v.col].vertices[adj_v.orientation])] for p in Player for adj_v in tiles[row_idx][col_idx].vertices[vo].adjacent_vertices) == 0)

def dev_card_player_scoring(type: TileType):
    return {
        TileType.SHEEP: 10,
        TileType.WHEAT: 10,
        TileType.ORE: 10,
        TileType.BRICK: 3,
        TileType.WOOD: 3,
        TileType.DESERT: 0
    }[type]

def dev_card_player_constraint(settlements: dict, canonical_vertices: dict, model: Model):
    # want to prioritize wheat, sheep, and ore specifically.
    model.setObjective(
            gp.quicksum(
                dev_card_player_scoring(vertex.tile.type) * settlements[Player.RED][id(vertex)]
                for vertex in canonical_vertices.values()
            ),
            GRB.MAXIMIZE
        )
    
def road_player_scoring(type: TileType):
    return {
        TileType.SHEEP: 3,
        TileType.WHEAT: 3,
        TileType.ORE: 3,
        TileType.BRICK: 10,
        TileType.WOOD: 10,
        TileType.DESERT: 0
    }[type]

def road_building_player_constraint(roads: dict, canonical_edges: dict, model: Model):
    # want to prioritize brick and wood specifically.
    model.setObjective(
            gp.quicksum(
                road_player_scoring(edge.tile.type) * roads[Player.PURPLE][id(edge)]
                for edge in canonical_edges.values()
            ),
            GRB.MAXIMIZE
        )
    
def port_building_player_constraint(settlements: dict, canonical_vertices: dict, model: Model):
    # must be on at least one port
    model.addConstr(
        gp.quicksum(
            ((1 if vertex.port else 0) * settlements[Player.BLUE][id(vertex)] for vertex in canonical_vertices.values())
        )
        >= 1
    )
    # want to the resources of the ports the player owns
    model.setObjective(
            gp.quicksum(
                (1 if other_v.tile.type == port_v.tile.type else 0) * settlements[Player.BLUE][id(port_v)] 
                for port_v in canonical_vertices.values()
                for other_v in canonical_vertices.values()
            ),
            GRB.MAXIMIZE
        )

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
        roads[player] = model.addVars(canonical_edges.keys(), vtype=GRB.BINARY, name="roads")
        settlements[player] = model.addVars(canonical_vertices.keys(), vtype=GRB.BINARY, name="settlements")

    two_settlements_two_roads_constraint(settlements, roads, model)
    no_overlaps_constraint(tiles, settlements, roads, model)
    road_connected_settlement_constraint(tiles, settlements, roads, model)
    settlement_distance_constraint(tiles, settlements, model)
    dev_card_player_constraint(settlements, canonical_vertices, model)
    road_building_player_constraint(roads, canonical_edges, model)
    port_building_player_constraint(settlements, canonical_vertices, model)

    # all players generally want higher numbers
    for p in Player:
        model.setObjective(
            gp.quicksum(
                probability_score(vertex.tile.dice) * settlements[p][id(vertex)]
                for vertex in canonical_vertices.values()
            ),
            GRB.MAXIMIZE
        )

    model.optimize()
    if model.status == GRB.INFEASIBLE:
        print("Model is infeasible, computing IIS...")
        model.computeIIS()
        model.write("infeasible.ilp")  # writes the conflicting constraints to a file

    assert model.status == GRB.OPTIMAL

    for player in Player:
        for key, var in settlements[player].items():
            if var.x == 1:  # binary var is 1
                canonical_vertices[key].settlement_placed = Settlement(player)
                # print(f"Player {player} settlement at {key}")
        for key, var in roads[player].items():
            if var.x == 1:
                canonical_edges[key].road_placed = Road(player)
                # print(f"Player {player} road at {key}")
    