import csv
from main import run


def get_status_meaning(status_code: int):
    """Converts a Gurobi status code to a human-readable string."""
    return {
        2: "OPTIMAL",
        3: "INFEASIBLE",
    }[status_code]

def evaluate():
    """Runs the model for a range of parameters and saves the results to a CSV file."""
    results = {
        "status": [],
        "runtime": [],
        "solution gap": [],
        "best bound": [],
        "num_constraints": []
    }
    player_counts = range(3, 7)
    road_settlement_counts = range(2, 7)
    for pc in player_counts:
        for rsc in road_settlement_counts:
            model = run(pc, rsc, eval_mode=True)
            results["status"].append(model.status)
            results["runtime"].append(model.Runtime)
            results["solution gap"].append(model.MIPGap)
            results["best bound"].append(model.ObjBound)
            results["num_constraints"].append(model.NumConstrs)

    with open('results.csv', 'w', newline='') as csvfile:
        fieldnames = ["player_count", "road_settlement_count", "status", "runtime", "solution gap", "best bound", "num_constraints"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        idx = 0
        for pc in player_counts:
            for rsc in road_settlement_counts:
                writer.writerow({
                    "player_count": pc,
                    "road_settlement_count": rsc,
                    "status": get_status_meaning(results["status"][idx]),
                    "runtime": round(results["runtime"][idx], 2),
                    "solution gap": results["solution gap"][idx],
                    "best bound": results["best bound"][idx],
                    "num_constraints": results["num_constraints"][idx]
                })
                idx += 1      

if __name__ == "__main__":
    evaluate()