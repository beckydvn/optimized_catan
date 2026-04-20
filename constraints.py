from board import BOARD_LAYOUT, Tile, EDGE_ORIENTATION, VERTEX_ORIENTATION, Player, Settlement, Road, TileType
from gurobipy import GRB
import gurobipy as gp

class Constraints:
    def __init__(self, tiles: list[list[Tile]], player_count: int, road_count: int, settlement_count: int):
        self.tiles = tiles
        self.player_count = player_count
        self.road_count = road_count
        self.settlement_count = settlement_count
        self.players = [p for p in Player][:player_count]
        self.model = gp.Model(f"Catan Constraints")
        self.canonical_edges = {}
        self.canonical_vertices = {}

        for row_idx in BOARD_LAYOUT:
            for col_idx in range(BOARD_LAYOUT[row_idx]):
                for o in EDGE_ORIENTATION:
                    edge = self.tiles[row_idx][col_idx].edges[o]
                    self.canonical_edges[id(edge)] = edge  # duplicate ids just overwrite, no error
                for vo in VERTEX_ORIENTATION:
                    vertex = self.tiles[row_idx][col_idx].vertices[vo]
                    self.canonical_vertices[id(vertex)] = vertex
        self.roads = {}
        self.settlements = {}

        # now pass only unique keys to gurobi
        for player in self.players:
            self.roads[player] = self.model.addVars(self.canonical_edges.keys(), vtype=GRB.BINARY, name="roads")
            self.settlements[player] = self.model.addVars(self.canonical_vertices.keys(), vtype=GRB.BINARY, name="settlements")

    @staticmethod
    def probability_score(value: int):
        return {
            7: 0,
            2: 3,
            12: 3,
            3: 9,
            11: 9,
            4: 27,
            10: 27,
            5: 81,
            9: 81,
            6: 243,
            8: 243
        }[value]

    def two_settlements_two_roads_constraint(self):
        # every player places exactly 2 roads and 2 settlements
        for player in self.players:
            self.model.addConstr(self.settlements[player].sum() == self.settlement_count)
            self.model.addConstr(self.roads[player].sum() == self.road_count)

    def no_overlaps_constraint(self):
        # settlements can't be placed on the same vertex and roads can't be placed on the same edge
        for row_idx in BOARD_LAYOUT:
            for col_idx in range(BOARD_LAYOUT[row_idx]):
                for o in EDGE_ORIENTATION:
                    self.model.addConstr(gp.quicksum(self.roads[p][id(self.tiles[row_idx][col_idx].edges[o])] for p in self.players)  <= 1)
                for vo in VERTEX_ORIENTATION:
                    self.model.addConstr(gp.quicksum(self.settlements[p][id(self.tiles[row_idx][col_idx].vertices[vo])] for p in self.players) <= 1)

    def settlement_connected_road_constraint(self):
        # all settlements must be connected to a road also owned by that player
        for row_idx in BOARD_LAYOUT:
            for col_idx in range(BOARD_LAYOUT[row_idx]):
                for vo in VERTEX_ORIENTATION:
                    for p in self.players:
                        self.model.addGenConstrIndicator(self.settlements[p][id(self.tiles[row_idx][col_idx].vertices[vo])], True, gp.quicksum(self.roads[p][id(adj_e)] for adj_e in self.tiles[row_idx][col_idx].vertices[vo].adjacent_edges) >= 1)

    def road_connected_settlement_constraint(self):
        # all settlements must be connected to a road also owned by that player
        for row_idx in BOARD_LAYOUT:
            for col_idx in range(BOARD_LAYOUT[row_idx]):
                for o in EDGE_ORIENTATION:
                    for p in self.players:
                        self.model.addGenConstrIndicator(
                            self.roads[p][id(self.tiles[row_idx][col_idx].edges[o])], 
                            True, 
                            gp.quicksum(self.settlements[p][id(adj_v)] for adj_v in self.tiles[row_idx][col_idx].edges[o].adjacent_vertices) +  \
                            gp.quicksum(self.roads[p][id(adj_e)] for adj_e in self.tiles[row_idx][col_idx].edges[o].adjacent_edges) >= 1
                        )

    def settlement_distance_constraint(self):
        for row_idx in BOARD_LAYOUT:
            for col_idx in range(BOARD_LAYOUT[row_idx]):
                for vo in VERTEX_ORIENTATION:
                    for player in self.players:
                        self.model.addGenConstrIndicator(
                            self.settlements[player][id(self.tiles[row_idx][col_idx].vertices[vo])], 
                            True, 
                            gp.quicksum(self.settlements[p][id(self.tiles[adj_v.row][adj_v.col].vertices[adj_v.orientation])] for p in self.players for adj_v in self.tiles[row_idx][col_idx].vertices[vo].adjacent_vertices) == 0
                        )

    def maximize_resource_diversity(self):
        for p in self.players:
            # want to prioritize wheat, sheep, and ore specifically.
            self.model.setObjective(
                len({(vertex.tile.type) for vertex in self.canonical_vertices.values() if self.settlements[p][id(vertex)]}),
                    GRB.MAXIMIZE
                )

    @staticmethod
    def dev_card_player_scoring(type: TileType):
        return {
            TileType.SHEEP: 243,
            TileType.WHEAT: 243,
            TileType.ORE: 243,
            TileType.BRICK: 27,
            TileType.WOOD: 27,
            TileType.DESERT: 0
        }[type]

    def dev_card_player_constraint(self):
        # want to prioritize wheat, sheep, and ore specifically.
        self.model.setObjective(
                gp.quicksum(
                    Constraints.dev_card_player_scoring(vertex.tile.type) * self.settlements[Player.PURPLE][id(vertex)]
                    for vertex in self.canonical_vertices.values()
                ),
                GRB.MAXIMIZE
            )
        for p in self.players:
            if p == Player.PURPLE:
                continue
            self.model.addConstr(
                gp.quicksum(
                    Constraints.dev_card_player_scoring(vertex.tile.type) * self.settlements[Player.PURPLE][id(vertex)]
                    for vertex in self.canonical_vertices.values()
                )
                >=
                gp.quicksum(
                    Constraints.dev_card_player_scoring(vertex.tile.type) * self.settlements[p][id(vertex)]
                    for vertex in self.canonical_vertices.values()
                )
            )
    
    @staticmethod
    def road_player_scoring(type: TileType):
        return {
            TileType.SHEEP: 27,
            TileType.WHEAT: 27,
            TileType.ORE: 27,
            TileType.BRICK: 243,
            TileType.WOOD: 243,
            TileType.DESERT: 0
        }[type]

    def road_building_player_constraint(self):
        # want to prioritize brick and wood specifically.
        self.model.setObjective(
            gp.quicksum(
                Constraints.road_player_scoring(edge.tile.type) * self.roads[Player.RED][id(edge)]
                for edge in self.canonical_edges.values()
            ),
            GRB.MAXIMIZE
        )
        for p in self.players:
            if p == Player.RED:
                continue
            self.model.addConstr(
                gp.quicksum(
                    Constraints.road_player_scoring(edge.tile.type) * self.roads[Player.RED][id(edge)]
                    for edge in self.canonical_edges.values()
                )
                >=
                gp.quicksum(
                    Constraints.road_player_scoring(edge.tile.type) * self.roads[p][id(edge)]
                    for edge in self.canonical_edges.values()
                )
            )
        
    def port_building_player_constraint(self):
        # must be on at least one port
        self.model.addConstr(
            gp.quicksum(
                (100 if vertex.port else 0) * self.settlements[Player.BLUE][id(vertex)] for vertex in self.canonical_vertices.values()
            )
            >= 1
        )
        # want to maximize the resources of the ports the player owns
        self.model.setObjective(
            gp.quicksum(
                (100 if other_v.tile.type == port_v.tile.type else 0) * self.settlements[Player.BLUE][id(port_v)] 
                for port_v in self.canonical_vertices.values()
                for other_v in self.canonical_vertices.values()
            ),
            GRB.MAXIMIZE
        )
        for p in self.players:
            if p == Player.BLUE:
                continue
            self.model.addConstr(
                gp.quicksum(
                    (100 if vertex.port else 0) * self.settlements[Player.BLUE][id(vertex)] for vertex in self.canonical_vertices.values()
                )
                >=
                gp.quicksum(
                    (100 if vertex.port else 0) * self.settlements[p][id(vertex)] for vertex in self.canonical_vertices.values()
                )
            )

    def generate_constraints(self):
        self.two_settlements_two_roads_constraint()
        self.no_overlaps_constraint()
        self.settlement_connected_road_constraint()
        self.road_connected_settlement_constraint()
        self.settlement_distance_constraint()
        self.maximize_resource_diversity()
        self.dev_card_player_constraint()
        self.road_building_player_constraint()
        self.port_building_player_constraint()

        # all players generally want higher numbers
        for p in self.players:
            self.model.setObjective(
                gp.quicksum(
                    self.probability_score(vertex.tile.dice) * self.settlements[p][id(vertex)]
                    for vertex in self.canonical_vertices.values()
                ),
                GRB.MAXIMIZE
            )

        self.model.optimize()
        if self.model.status == GRB.INFEASIBLE:
            print("Model is infeasible, computing IIS...")
            self.model.computeIIS()
            self.model.write("infeasible.ilp")  # writes the conflicting constraints to a file

        assert self.model.status == GRB.OPTIMAL

        for player in self.players:
            for key, var in self.settlements[player].items():
                if var.x == 1:  # binary var is 1
                    self.canonical_vertices[key].settlement_placed = Settlement(player)
            for key, var in self.roads[player].items():
                if var.x == 1:
                    self.canonical_edges[key].road_placed = Road(player)
        