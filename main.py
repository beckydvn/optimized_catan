from board import game_setup
from gui import draw
from constraints import Constraints
import csv
# import sys
# import matplotlib.pyplot as plt

def run(player_count: int, road_count: int, settlement_count: int, eval_mode: bool = False):
    if player_count < 3 or player_count > 6 or road_count < 2 or road_count > 6 or settlement_count < 2 or settlement_count > 4:
        raise ValueError("Invalid arguments. Please provide a player count (from 3 - 6), a road count (from 2 - 6), and a settlement count (from 2 - 4).")
    tiles = game_setup()
    constraint = Constraints(tiles, player_count, road_count, settlement_count)
    constraint.generate_constraints(evaluate_only=eval_mode)
    if not eval_mode:
        draw(tiles)
    return constraint.model

# def plot_stats(results: dict, object_counts: range):
#     # make plots comparing player count against each parameter
#     stats = ["status", "runtime", "solution gap", "best bound", "num_constraints"]
    
#     fig, axes = plt.subplots(len(stats), 1, figsize=(8, 4 * len(stats)))
    
#     for ax, stat in zip(axes, stats):
#         ax.plot(object_counts, results[stat], marker='o')
#         ax.set_title(stat)
#         ax.set_xlabel("Road/settlement count")
#         ax.set_ylabel(stat)
#         ax.set_xticks(object_counts)
#         ax.grid(True)
    
#     plt.tight_layout()
#     plt.show()

def get_status_meaning(status_code: int):
    return {
        2: "OPTIMAL",
        3: "INFEASIBLE",
    }[status_code]

def evaluate():
    results = {
        "status": [],
        "runtime": [],
        "solution gap": [],
        "best bound": [],
        "num_constraints": []
    }
    # road_count = 2
    # settlement_count = 2
    # player_count = 4
    player_counts = range(3, 7)
    road_counts = range(2, 7)
    settlement_counts = range(2, 5)
    for pc in player_counts:
        for rc in road_counts:
            for sc in settlement_counts:
                model = run(pc, rc, sc, eval_mode=True)
                results["status"].append(model.status)
                results["runtime"].append(model.Runtime)
                results["solution gap"].append(model.MIPGap)
                results["best bound"].append(model.ObjBound)
                results["num_constraints"].append(model.NumConstrs)

    with open('results.csv', 'w', newline='') as csvfile:
        fieldnames = ["player_count", "road_count", "settlement_count", "status", "runtime", "solution gap", "best bound", "num_constraints"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        idx = 0
        for pc in player_counts:
            for rc in road_counts:
                for sc in settlement_counts:
                    writer.writerow({
                        "player_count": pc,
                        "road_count": rc,
                        "settlement_count": sc,
                        "status": get_status_meaning(results["status"][idx]),
                        "runtime": round(results["runtime"][idx], 2),
                        "solution gap": results["solution gap"][idx],
                        "best bound": results["best bound"][idx],
                        "num_constraints": results["num_constraints"][idx]
                    })
                    idx += 1

    # plot_stats(results, object_counts)
      

if __name__ == "__main__":
    evaluate()
    # run as: python main 3 6 4 (or similar)
    # player_count = int(sys.argv[1])
    # road_count = int(sys.argv[2])
    # settlement_count = int(sys.argv[3])
    
    # run(player_count, road_count, settlement_count, eval_mode=False)