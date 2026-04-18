import gurobipy as gp
from gurobipy import GRB
# Print version
print(f"Gurobi version: {gp.gurobi.version()}")
# Create a simple model to test
m = gp.Model("test")
x = m.addVar(name="x")
listtest = [1, 2, 10]
m.setObjective(x, GRB.MAXIMIZE)
m.addConstr(x in listtest)
m.optimize()
print(f"Optimal value: {x.X}")
print("Gurobi is working correctly!")