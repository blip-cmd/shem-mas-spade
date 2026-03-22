"""Plot evaluation results produced by the Day 6 stress test."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_evaluation_data(csv_path: Path) -> dict:
	"""Load all evaluation metrics from the stress test CSV."""
	data = {
		"solar_cycles": [],
		"state_transitions": [],
	}

	with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
		reader = csv.DictReader(csv_file)
		for row in reader:
			timestep = row.get("timestep")
			if not timestep:
				continue

			ts = int(timestep)
			if ts < 0:
				continue

			event_type = row.get("event_type", "")
			if event_type == "solar_cycle":
				data["solar_cycles"].append(
					{
						"timestep": ts,
						"phase": row.get("phase", ""),
						"wattage": float(row.get("wattage") or 0.0),
						"grid_energy": float(row.get("grid_energy_saved_units") or 0.0),
					}
				)
			elif event_type == "state_transition":
				reaction_time_raw = row.get("reaction_time_ms", "")
				data["state_transitions"].append(
					{
						"timestep": ts,
						"phase": row.get("phase", ""),
						"battery_level": float(row.get("battery_level") or 0.0),
						"battery_health": row.get("battery_health", ""),
						"wattage": float(row.get("wattage") or 0.0),
						"grid_energy": float(row.get("grid_energy_saved_units") or 0.0),
						"safety_violation": int(row.get("safety_violation") or 0),
						"reaction_time_ms": float(reaction_time_raw) if reaction_time_raw else None,
					}
				)

	return data


def plot_stress_test_dashboard(csv_path: Path, output_path: Path) -> None:
	"""Generate a comprehensive stress test evaluation dashboard."""
	data = load_evaluation_data(csv_path)
	if not data["solar_cycles"] and not data["state_transitions"]:
		raise ValueError("No evaluation rows found in evaluation CSV.")

	# Focus dashboard on the Day 6 stress window when available.
	stress_solar = [row for row in data["solar_cycles"] if 0 <= row["timestep"] <= 24]
	stress_transitions = [row for row in data["state_transitions"] if 0 <= row["timestep"] <= 24]
	if stress_solar:
		solar_rows = stress_solar
		transition_rows = stress_transitions
	else:
		solar_rows = data["solar_cycles"]
		transition_rows = data["state_transitions"]

	# Extract unique timestep entries and aggregate by phase
	timesteps = sorted(
		set([row["timestep"] for row in solar_rows] + [row["timestep"] for row in transition_rows])
	)
	if not timesteps:
		raise ValueError("No valid timestep data found.")

	phase_by_ts = {}
	for row in solar_rows:
		phase_by_ts[row["timestep"]] = row["phase"]
	for row in transition_rows:
		phase_by_ts.setdefault(row["timestep"], row["phase"])

	def get_phase_name(ts: int) -> str:
		return phase_by_ts.get(ts, "ZERO_SUNLIGHT")

	# Aggregate metrics by phase
	phase_stats = {"HIGH_SUNLIGHT": {}, "CLOUD_STRESS": {}, "ZERO_SUNLIGHT": {}}
	phase_colors = {
		"HIGH_SUNLIGHT": "#FFD700",
		"CLOUD_STRESS": "#A9A9A9",
		"ZERO_SUNLIGHT": "#191970",
	}

	for phase_name in phase_stats:
		phase_solar = [row for row in solar_rows if get_phase_name(row["timestep"]) == phase_name]
		phase_transitions = [
			row for row in transition_rows if get_phase_name(row["timestep"]) == phase_name
		]
		phase_reaction_samples = [
			row["reaction_time_ms"]
			for row in phase_transitions
			if row["reaction_time_ms"] is not None
		]
		phase_stats[phase_name] = {
			"avg_battery": np.mean([row["battery_level"] for row in phase_transitions])
			if phase_transitions
			else 0.0,
			"total_grid_energy": sum(row["grid_energy"] for row in phase_solar)
			+ sum(row["grid_energy"] for row in phase_transitions),
			"safety_violations": sum(row["safety_violation"] for row in phase_transitions),
			"avg_reaction_time": np.mean(phase_reaction_samples)
			if phase_reaction_samples
			else 0.0,
		}

	# Aggregate battery values per timestep for a more informative plot.
	battery_by_ts = {}
	for row in transition_rows:
		ts = row["timestep"]
		battery_by_ts.setdefault(ts, []).append(row["battery_level"])

	wattage_by_ts = {row["timestep"]: row["wattage"] for row in solar_rows}

	sorted_ts = sorted(battery_by_ts.keys())
	sorted_battery_min = [min(battery_by_ts[ts]) for ts in sorted_ts]
	sorted_battery_max = [max(battery_by_ts[ts]) for ts in sorted_ts]
	sorted_battery_avg = [float(np.mean(battery_by_ts[ts])) for ts in sorted_ts]
	sorted_wattage = [wattage_by_ts.get(ts, 0.0) for ts in sorted_ts]

	# Create dashboard
	fig = plt.figure(figsize=(14, 12))
	gs = fig.add_gridspec(3, 2, hspace=0.45, wspace=0.3)

	# Plot 1: Battery Level Over Time
	ax1 = fig.add_subplot(gs[0, :])
	ax1.fill_between(
		sorted_ts,
		sorted_battery_min,
		sorted_battery_max,
		color="#1f77b4",
		alpha=0.2,
		label="Battery range (min-max)",
	)
	ax1.plot(
		sorted_ts,
		sorted_battery_avg,
		marker="o",
		linewidth=2.5,
		color="#1f77b4",
		markersize=4,
		label="Battery average",
	)
	phase_segments = []
	if sorted_ts:
		seg_start = sorted_ts[0]
		seg_phase = get_phase_name(sorted_ts[0])
		prev_ts = sorted_ts[0]
		for ts in sorted_ts[1:]:
			curr_phase = get_phase_name(ts)
			if curr_phase != seg_phase:
				phase_segments.append((seg_start, prev_ts, seg_phase))
				seg_start = ts
				seg_phase = curr_phase
			prev_ts = ts
		phase_segments.append((seg_start, prev_ts, seg_phase))

	added_labels = set()
	for seg_start, seg_end, seg_phase in phase_segments:
		if seg_phase not in phase_colors:
			continue
		label = seg_phase if seg_phase not in added_labels else None
		ax1.axvspan(seg_start, seg_end, alpha=0.1, color=phase_colors[seg_phase], label=label)
		added_labels.add(seg_phase)
	ax1.set_title("Battery Level Across Stress Test Phases", fontsize=12, fontweight="bold")
	ax1.set_xlabel("Timestep")
	ax1.set_ylabel("Battery Level (%)")
	ax1.grid(True, linestyle="--", alpha=0.3)
	ax1.legend(loc="upper right", fontsize=9)
	batt_min = min(sorted_battery_min)
	batt_max = max(sorted_battery_max)
	if batt_min == batt_max:
		ax1.set_ylim(max(0, batt_min - 5), min(100, batt_max + 5))
	else:
		padding = max(1.0, (batt_max - batt_min) * 0.2)
		ax1.set_ylim(max(0, batt_min - padding), min(100, batt_max + padding))

	# Plot 2: Solar Wattage Input
	ax2 = fig.add_subplot(gs[1, 0])
	ax2.bar(
		sorted_ts,
		sorted_wattage,
		color=[phase_colors.get(get_phase_name(ts), "#191970") for ts in sorted_ts],
		alpha=0.7,
	)
	ax2.set_title("Solar Wattage by Phase", fontsize=11, fontweight="bold")
	ax2.set_xlabel("Timestep")
	ax2.set_ylabel("Wattage (W)")
	ax2.grid(True, linestyle="--", alpha=0.3, axis="y")

	# Plot 3: System Performance Metrics
	ax3 = fig.add_subplot(gs[1, 1])
	phases = list(phase_stats.keys())
	grid_energy_vals = [
		phase_stats[p].get("total_grid_energy", 0) for p in phases
	]
	colors_list = [phase_colors[p] for p in phases]
	bars = ax3.bar(phases, grid_energy_vals, color=colors_list, alpha=0.7)
	ax3.set_title("Total Grid Energy Saved", fontsize=11, fontweight="bold")
	ax3.set_ylabel("Energy Units")
	ax3.grid(True, linestyle="--", alpha=0.3, axis="y")
	# Add value labels on bars
	for bar in bars:
		height = bar.get_height()
		ax3.text(
			bar.get_x() + bar.get_width() / 2,
			height,
			f"{height:.1f}",
			ha="center",
			va="bottom",
			fontsize=9,
		)

	# Plot 4: Safety Violations
	ax4 = fig.add_subplot(gs[2, 0])
	violation_vals = [
		phase_stats[p].get("safety_violations", 0) for p in phases
	]
	bars = ax4.bar(phases, violation_vals, color=colors_list, alpha=0.7)
	ax4.set_title("Battery Safety Violations", fontsize=11, fontweight="bold")
	ax4.set_ylabel("Violations Count")
	ax4.grid(True, linestyle="--", alpha=0.3, axis="y")
	# Add value labels on bars
	for bar in bars:
		height = bar.get_height()
		ax4.text(
			bar.get_x() + bar.get_width() / 2,
			height,
			f"{int(height)}",
			ha="center",
			va="bottom",
			fontsize=9,
		)

	# Plot 5: Average Reaction Time
	ax5 = fig.add_subplot(gs[2, 1])
	reaction_vals = [
		phase_stats[p].get("avg_reaction_time", 0) for p in phases
	]
	bars = ax5.bar(phases, reaction_vals, color=colors_list, alpha=0.7)
	ax5.set_title("Average Reaction Time", fontsize=11, fontweight="bold")
	ax5.set_ylabel("Reaction Time (ms)")
	ax5.grid(True, linestyle="--", alpha=0.3, axis="y")
	# Add value labels on bars
	for bar in bars:
		height = bar.get_height()
		ax5.text(
			bar.get_x() + bar.get_width() / 2,
			height,
			f"{height:.3f}",
			ha="center",
			va="bottom",
			fontsize=9,
		)

	fig.suptitle(
		"SHEM Stress Test Evaluation Dashboard",
		fontsize=14,
		fontweight="bold",
		y=0.98,
	)
	plt.savefig(output_path, dpi=150, bbox_inches="tight")
	plt.close()


def main() -> None:
	"""Read evaluation_results.csv and generate stress test dashboard."""
	csv_path = Path("evaluation_results.csv")
	output_path = Path("battery_level_over_time.png")

	if not csv_path.exists():
		raise FileNotFoundError(
			"evaluation_results.csv was not found. Run the stress test before plotting results."
		)

	plot_stress_test_dashboard(csv_path, output_path)
	print(f"Saved stress test dashboard to {output_path}")


if __name__ == "__main__":
	main()