# FastBox Mystery Delivery System

A Python simulator for one day of operations at a fictional delivery company, **FastBox**. Given a set of warehouses, delivery agents, and packages, the program assigns each package to the nearest agent, simulates the day's deliveries, and generates a performance report.

## Features

- **JSON parsing** — reads warehouse, agent, and package data from a JSON file. Supports both dict-style (`{"W1": [x, y]}`) and list-style (`[{"id": "W1", "location": [x, y]}]`) input formats.
- **Nearest-agent assignment** — assigns each package to the delivery agent closest to its warehouse, using Euclidean distance.
- **Delivery simulation** — routes each agent from its current position → warehouse → destination for every assigned package, tracking total distance traveled.
- **Report generation** — outputs `report.json` with packages delivered, total distance, and efficiency (average distance per package) for every agent, plus the overall `best_agent`.
- **Bonus features**:
  - Optional random delivery delays
  - ASCII map visualization of warehouses and agents
  - Support for a new agent joining mid-day
  - CSV export of the top-performing agent

## Usage

```bash
python3 delivery_system.py
```

By default this reads `data.json` in the current directory and writes `report.json` and `top_performer.csv`.

To use it programmatically:

```python
from delivery_system import run

report = run(
    input_file="data.json",
    report_file="report.json",
    csv_file="top_performer.csv",
    with_delays=False,
    print_map=True,
)
```

## Input format

```json
{
  "warehouses": { "W1": [0, 0], "W2": [50, 75], "W3": [100, 25] },
  "agents": { "A1": [5, 5], "A2": [60, 60], "A3": [95, 30] },
  "packages": [
    { "id": "P1", "warehouse": "W1", "destination": [30, 40] }
  ]
}
```

## Output format (`report.json`)

```json
{
  "A1": { "packages_delivered": 2, "total_distance": 121.21, "efficiency": 60.61 },
  "A2": { "packages_delivered": 2, "total_distance": 79.21, "efficiency": 39.6 },
  "A3": { "packages_delivered": 1, "total_distance": 14.14, "efficiency": 14.14 },
  "best_agent": "A3"
}
```

## Logic assumptions

- Ties in agent distance are broken by insertion order (no explicit tie-break rule).
- Packages are delivered in the order they appear in the input file.
- Each package incurs a fresh trip to its warehouse from the agent's current position, even if a prior package came from the same warehouse.
- "Efficiency" = total distance ÷ packages delivered (lower is better); `best_agent` is the agent with the lowest efficiency.

## Files

- `delivery_system.py` — main script
- `data.json` — sample input (from the assignment PDF)
- `report.json` — generated report for the sample input
- `top_performer.csv` — CSV export of the top-performing agent
