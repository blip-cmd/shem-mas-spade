"""Plot evaluation results produced by the Day 6 stress test."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt


def load_battery_series(csv_path: Path) -> tuple[list[int], list[float]]:
	"""Load battery levels from state-transition rows in the evaluation CSV."""
	timesteps: list[int] = []
	battery_levels: list[float] = []

	with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
		reader = csv.DictReader(csv_file)
		for row in reader:
			battery_level = row.get("battery_level")
			timestep = row.get("timestep")
			if not battery_level or not timestep:
				continue
			timesteps.append(int(timestep))
			battery_levels.append(float(battery_level))

	return timesteps, battery_levels


def plot_battery_levels(csv_path: Path, output_path: Path) -> None:
	"""Generate and save a battery-level-over-time chart."""
	timesteps, battery_levels = load_battery_series(csv_path)
	if not timesteps:
		raise ValueError("No battery transition rows were found in the evaluation CSV.")

	plt.figure(figsize=(10, 5))
	plt.plot(timesteps, battery_levels, marker="o", linewidth=2, color="#1f77b4")
	plt.title("SHEM Battery Level Over Time")
	plt.xlabel("Timestep")
	plt.ylabel("Battery Level (%)")
	plt.grid(True, linestyle="--", alpha=0.4)
	plt.tight_layout()
	plt.savefig(output_path, dpi=150)
	plt.close()


def main() -> None:
	"""Read evaluation_results.csv and write battery_level_over_time.png."""
	csv_path = Path("evaluation_results.csv")
	output_path = Path("battery_level_over_time.png")

	if not csv_path.exists():
		raise FileNotFoundError(
			"evaluation_results.csv was not found. Run the stress test before plotting results."
		)

	plot_battery_levels(csv_path, output_path)
	print(f"Saved plot to {output_path}")


if __name__ == "__main__":
	main()