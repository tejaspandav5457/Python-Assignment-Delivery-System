"""
FastBox Mystery Delivery System
--------------------------------
Simulates one day of FastBox delivery operations:
  1. Reads and parses the warehouse / agent / package data from a JSON file.
  2. Assigns every package to the delivery agent nearest to its warehouse
     (Euclidean distance from agent -> warehouse).
  3. Simulates each agent's route (start -> warehouse -> destination for
     every assigned package, in order) and totals the distance travelled.
  4. Builds a report of packages delivered, total distance and "efficiency"
     (average distance per package) for every agent, plus the best agent.
  5. Saves the report to report.json.

Bonus features included:
  - Optional random delivery delays (extra distance/time per delivery).
  - ASCII map of warehouses and agents.
  - Support for a new agent joining mid-day.
  - CSV export of the top-performing agent.

The script accepts both JSON layouts seen in the sample data:
  * dict style   -> {"W1": [x, y], ...}                (warehouses/agents)
                    {"id": "P1", "warehouse": "W1", ...} (packages)
  * list style   -> [{"id": "W1", "location": [x, y]}, ...]
                    {"id": "P1", "warehouse_id": "W1", ...}
"""

import json
import math
import random
import csv


# ---------------------------------------------------------------------------
# 1. Read & parse the input JSON
# ---------------------------------------------------------------------------
def load_data(filepath):
    """Load warehouses, agents and packages from a JSON file and normalise
    them into a common, simple structure regardless of which of the two
    input layouts was used.

    Returns:
        warehouses: dict {id: (x, y)}
        agents:     dict {id: (x, y)}
        packages:   list of {"id", "warehouse", "destination": (x, y)}
    """
    with open(filepath, "r") as f:
        raw = json.load(f)

    def normalise_points(section):
        """Handle both {'W1': [x, y]} and [{'id': 'W1', 'location': [x, y]}]."""
        points = {}
        if isinstance(section, dict):
            for pid, loc in section.items():
                points[pid] = tuple(loc)
        else:
            for item in section:
                points[item["id"]] = tuple(item["location"])
        return points

    warehouses = normalise_points(raw["warehouses"])
    agents = normalise_points(raw["agents"])

    packages = []
    for p in raw["packages"]:
        warehouse_id = p.get("warehouse", p.get("warehouse_id"))
        packages.append({
            "id": p["id"],
            "warehouse": warehouse_id,
            "destination": tuple(p["destination"]),
        })

    return warehouses, agents, packages


# ---------------------------------------------------------------------------
# 2. Distance helper
# ---------------------------------------------------------------------------
def euclidean(point_a, point_b):
    """Straight-line distance between two (x, y) points."""
    return math.sqrt((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2)


# ---------------------------------------------------------------------------
# 3. Assign each package to its nearest agent
# ---------------------------------------------------------------------------
def assign_packages(warehouses, agents, packages):
    """Assign every package to whichever agent is closest to that
    package's warehouse (Euclidean distance)."""
    assignments = {agent_id: [] for agent_id in agents}
    for pkg in packages:
        warehouse_loc = warehouses[pkg["warehouse"]]
        nearest_agent = min(
            agents, key=lambda agent_id: euclidean(agents[agent_id], warehouse_loc)
        )
        assignments[nearest_agent].append(pkg)
    return assignments


# ---------------------------------------------------------------------------
# 4. Simulate the day and build the report
# ---------------------------------------------------------------------------
def simulate(warehouses, agents, assignments, with_delays=False):
    """Simulate each agent's route for the day.

    For each agent, starting from its initial position, we visit the
    warehouse and then the destination for every assigned package (in the
    order the packages appear), accumulating total distance travelled.
    """
    report = {}
    for agent_id, pkgs in assignments.items():
        current_pos = agents[agent_id]
        total_distance = 0.0
        delivered = 0

        for pkg in pkgs:
            warehouse_loc = warehouses[pkg["warehouse"]]
            dest_loc = pkg["destination"]

            total_distance += euclidean(current_pos, warehouse_loc)  # travel to warehouse
            total_distance += euclidean(warehouse_loc, dest_loc)     # deliver to destination

            if with_delays:
                # Bonus: a random delay modelled as small extra "distance"
                total_distance += random.uniform(0, 3)

            current_pos = dest_loc  # agent is now at the delivery point
            delivered += 1

        efficiency = round(total_distance / delivered, 2) if delivered else 0.0
        report[agent_id] = {
            "packages_delivered": delivered,
            "total_distance": round(total_distance, 2),
            "efficiency": efficiency,
        }

    return report


def add_best_agent(report):
    """Add the 'best_agent' key: the agent with the lowest average
    distance per package (i.e. most efficient), among agents who
    delivered at least one package."""
    active = {aid: r for aid, r in report.items() if r["packages_delivered"] > 0}
    report["best_agent"] = min(active, key=lambda aid: active[aid]["efficiency"]) if active else None
    return report


def save_report(report, filepath="report.json"):
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {filepath}")


# ---------------------------------------------------------------------------
# Bonus 1: ASCII visualisation of warehouses & agents
# ---------------------------------------------------------------------------
def ascii_map(warehouses, agents, size=20):
    all_points = list(warehouses.values()) + list(agents.values())
    max_x = max(p[0] for p in all_points) or 1
    max_y = max(p[1] for p in all_points) or 1
    grid = [[" "] * (size + 1) for _ in range(size + 1)]

    def place(loc, symbol):
        x = int(loc[0] / max_x * size)
        y = int(loc[1] / max_y * size)
        grid[size - y][x] = symbol  # flip y so higher y is drawn near the top

    for loc in warehouses.values():
        place(loc, "W")
    for loc in agents.values():
        place(loc, "A")

    return "\n".join("".join(row) for row in grid)


# ---------------------------------------------------------------------------
# Bonus 2: a new agent joining mid-day
# ---------------------------------------------------------------------------
def assign_with_midday_agent(warehouses, agents, packages, new_agent_id, new_agent_loc,
                              joins_after_package_index):
    """Same as assign_packages, but a new agent only becomes available for
    packages from `joins_after_package_index` onward (simulating them
    clocking in partway through the day)."""
    all_agents = dict(agents)
    assignments = {agent_id: [] for agent_id in all_agents}
    assignments[new_agent_id] = []

    for i, pkg in enumerate(packages):
        warehouse_loc = warehouses[pkg["warehouse"]]
        candidates = dict(all_agents)
        if i >= joins_after_package_index:
            candidates[new_agent_id] = new_agent_loc
        nearest_agent = min(candidates, key=lambda aid: euclidean(candidates[aid], warehouse_loc))
        assignments.setdefault(nearest_agent, []).append(pkg)

    all_agents[new_agent_id] = new_agent_loc
    return all_agents, assignments


# ---------------------------------------------------------------------------
# Bonus 3: export the top performer to CSV
# ---------------------------------------------------------------------------
def export_top_performer_csv(report, filepath="top_performer.csv"):
    best = report.get("best_agent")
    if not best:
        return
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["agent", "packages_delivered", "total_distance", "efficiency"])
        stats = report[best]
        writer.writerow([best, stats["packages_delivered"], stats["total_distance"], stats["efficiency"]])
    print(f"Top performer exported to {filepath}")


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------
def run(input_file="data.json", report_file="report.json", csv_file=None,
        with_delays=False, print_map=False):
    warehouses, agents, packages = load_data(input_file)
    assignments = assign_packages(warehouses, agents, packages)
    report = simulate(warehouses, agents, assignments, with_delays=with_delays)
    report = add_best_agent(report)

    # Sanity check required by the assignment: every package accounted for.
    total_delivered = sum(r["packages_delivered"] for aid, r in report.items() if aid != "best_agent")
    assert total_delivered == len(packages), "Not all packages were delivered!"

    save_report(report, report_file)
    if csv_file:
        export_top_performer_csv(report, csv_file)
    if print_map:
        print(ascii_map(warehouses, agents))

    return report


if __name__ == "__main__":
    result = run("data.json", report_file="report.json", csv_file="top_performer.csv", print_map=True)
    print(json.dumps(result, indent=2))
