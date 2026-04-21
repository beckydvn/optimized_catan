from board import BOARD_LAYOUT, Tile, EDGE_ORIENTATION, VERTEX_ORIENTATION, Player, Settlement, Road, TileType
from gurobipy import GRB
import gurobipy as gp

class Constraints:
    """This class defines the combinatorial optimization model for Catan, including the decision variables, constraints, and objective function."""
    def __init__(self, tiles: list[list[Tile]], player_count: int, road_settlement_count: int):
        self.tiles = tiles
        self.player_count = player_count
        self.road_settlement_count = road_settlement_count
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
        """Returns a score for a given dice value based on its probability of being rolled (higher probabilities are better, exponentially)."""
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

    def settlement_road_count_constraint(self):
        """Constraint: every player places exactly road_count roads and settlement_count settlements."""
        for player in self.players:
            self.model.addConstr(self.settlements[player].sum() == self.road_settlement_count)
            self.model.addConstr(self.roads[player].sum() == self.road_settlement_count)

    def no_overlaps_constraint(self):
        """Constraint: settlements can't be placed on the same vertex and roads can't be placed on the same edge."""
        for row_idx in BOARD_LAYOUT:
            for col_idx in range(BOARD_LAYOUT[row_idx]):
                for o in EDGE_ORIENTATION:
                    self.model.addConstr(gp.quicksum(self.roads[p][id(self.tiles[row_idx][col_idx].edges[o])] for p in self.players)  <= 1)
                for vo in VERTEX_ORIENTATION:
                    self.model.addConstr(gp.quicksum(self.settlements[p][id(self.tiles[row_idx][col_idx].vertices[vo])] for p in self.players) <= 1)

    def settlement_connected_road_constraint(self):
        """Constraint: all settlements must be connected to a road also owned by that player."""
        for row_idx in BOARD_LAYOUT:
            for col_idx in range(BOARD_LAYOUT[row_idx]):
                for vo in VERTEX_ORIENTATION:
                    for p in self.players:
                        self.model.addGenConstrIndicator(self.settlements[p][id(self.tiles[row_idx][col_idx].vertices[vo])], True, gp.quicksum(self.roads[p][id(adj_e)] for adj_e in self.tiles[row_idx][col_idx].vertices[vo].adjacent_edges) >= 1)

    def road_connected_settlement_constraint(self):
        """Constraint: all roads must be connected to a settlement also owned by that player."""
        for row_idx in BOARD_LAYOUT:
            for col_idx in range(BOARD_LAYOUT[row_idx]):
                for o in EDGE_ORIENTATION:
                    for p in self.players:
                        self.model.addGenConstrIndicator(
                            self.roads[p][id(self.tiles[row_idx][col_idx].edges[o])], 
                            True, 
                            gp.quicksum(self.settlements[p][id(adj_v)] for adj_v in self.tiles[row_idx][col_idx].edges[o].adjacent_vertices) >= 1
                        )

    def settlement_distance_constraint(self):
        """Constraint: settlements must be at least 2 vertices apart."""
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
        """Objective: maximize the diversity of resources for each player."""
        for p in self.players:
            self.model.setObjective(
                len({(vertex.tile.type) for vertex in self.canonical_vertices.values() if self.settlements[p][id(vertex)]}),
                    GRB.MAXIMIZE
                )

    @staticmethod
    def dev_card_player_scoring(type: TileType):
        """Returns scores for the player focusing on the development card victory point strategy, which prioritizes wheat, sheep, and ore."""
        return {
            TileType.SHEEP: 243,
            TileType.WHEAT: 243,
            TileType.ORE: 243,
            TileType.BRICK: 27,
            TileType.WOOD: 27,
            TileType.DESERT: 0
        }[type]

    def dev_card_player_constraint(self, dev_player: Player):
        """Objective: For the player focusing on the development card victory point strategy, maximize the number of wheat, sheep, and ore tiles they have settlements on.
        Constraint: This player must have at least as many wheat, sheep, and ore tiles as every other player."""
        # want to prioritize wheat, sheep, and ore specifically.
        self.model.setObjective(
                gp.quicksum(
                    Constraints.dev_card_player_scoring(vertex.tile.type) * self.settlements[dev_player][id(vertex)]
                    for vertex in self.canonical_vertices.values()
                ),
                GRB.MAXIMIZE
            )
        
        for p in self.players:
            if p == dev_player:
                continue
            self.model.addConstr(
                gp.quicksum(
                    Constraints.dev_card_player_scoring(vertex.tile.type) * self.settlements[dev_player][id(vertex)]
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
        """Returns scores for the player focusing on the longest road strategy, which prioritizes wood and brick."""
        return {
            TileType.SHEEP: 27,
            TileType.WHEAT: 27,
            TileType.ORE: 27,
            TileType.BRICK: 243,
            TileType.WOOD: 243,
            TileType.DESERT: 0
        }[type]

    def road_building_player_constraint(self, road_player: Player):
        """Objective: For the player focusing on the road building strategy, maximize the number of wood and brick tiles they have settlements on.
        Constraint: This player must have at least as many wood and brick tiles as every other player."""
        self.model.setObjective(
            gp.quicksum(
                Constraints.road_player_scoring(edge.tile.type) * self.roads[road_player][id(edge)]
                for edge in self.canonical_edges.values()
            ),
            GRB.MAXIMIZE
        )
        for p in self.players:
            if p == road_player:
                continue
            self.model.addConstr(
                gp.quicksum(
                    Constraints.road_player_scoring(edge.tile.type) * self.roads[road_player][id(edge)]
                    for edge in self.canonical_edges.values()
                )
                >=
                gp.quicksum(
                    Constraints.road_player_scoring(edge.tile.type) * self.roads[p][id(edge)]
                    for edge in self.canonical_edges.values()
                )
            )
        
    def port_building_player_constraint(self, port_player: Player):
        """Constraint: For the player focusing on the port building strategy, they must occupy at least one port.
        Objective: For the player focusing on the port building strategy, maximize the number of ports they have settlements on.
        Objective: For the player focusing on the port building strategy, maximize the number of resources they have access to relevant to their ports.
        Constraint: For the player focusing on the port building strategy, they must have at least as many ports as every other player."""
        # must be on at least one port
        self.model.addConstr(
            gp.quicksum(
                (100 if vertex.port else 0) * self.settlements[port_player][id(vertex)] for vertex in self.canonical_vertices.values()
            )
            >= 1
        )
        # want to maximize the resources of the ports the player owns
        self.model.setObjective(
            gp.quicksum(
                (100 if other_v.tile.type == port_v.tile.type else 0) * self.settlements[port_player][id(port_v)] 
                for port_v in self.canonical_vertices.values()
                for other_v in self.canonical_vertices.values()
            ),
            GRB.MAXIMIZE
        )
        for p in self.players:
            if p == port_player:
                continue
            self.model.addConstr(
                gp.quicksum(
                    (100 if vertex.port else 0) * self.settlements[port_player][id(vertex)] for vertex in self.canonical_vertices.values()
                )
                >=
                gp.quicksum(
                    (100 if vertex.port else 0) * self.settlements[p][id(vertex)] for vertex in self.canonical_vertices.values()
                )
            )

    def generate_constraints(self, evaluate_only = False):
        """Generate all the constraints for the model."""
        self.settlement_road_count_constraint()
        self.no_overlaps_constraint()
        self.settlement_connected_road_constraint()
        self.road_connected_settlement_constraint()
        self.settlement_distance_constraint()
        self.maximize_resource_diversity()

        for i in range(len(self.players)):
            if i in [1, 4]:
                self.road_building_player_constraint(self.players[i])
            elif i in [2, 5]:
                self.port_building_player_constraint(self.players[i])
            elif i in [3, 6]:
                self.dev_card_player_constraint(self.players[i])

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

        if not evaluate_only:
            if self.model.status == GRB.OPTIMAL:
                for player in self.players:
                    for key, var in self.settlements[player].items():
                        if var.x == 1:  # binary var is 1
                            self.canonical_vertices[key].settlement_placed = Settlement(player)
                    for key, var in self.roads[player].items():
                        if var.x == 1:
                            self.canonical_edges[key].road_placed = Road(player)
            elif self.model.status == GRB.INFEASIBLE:
                print("Model is infeasible, computing IIS...")
                self.model.computeIIS()
                self.model.write("infeasible.ilp")  # writes the conflicting constraints to a file
                
                # print the conflicting constraints directly
                for c in self.model.getConstrs():
                    if c.IISConstr:
                        print(f"Conflicting constraint: {c.constrName}")