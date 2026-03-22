"""Plot evaluation results produced by the Day 6 stress test."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
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
		row_index = 0
		for row in reader:
			row_index += 1
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
						"row_index": row_index,
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
						"row_index": row_index,
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


def build_timestep_snapshots(transition_rows: list[dict]) -> list[dict]:
	"""Collapse multiple FSM transitions into one snapshot per timestep."""
	by_timestep = defaultdict(list)
	for row in transition_rows:
		by_timestep[row["timestep"]].append(row)

	snapshots = []
	for timestep in sorted(by_timestep.keys()):
		rows = sorted(by_timestep[timestep], key=lambda item: item["row_index"])
		battery_values = [item["battery_level"] for item in rows]
		reaction_samples = [
			item["reaction_time_ms"] for item in rows if item["reaction_time_ms"] is not None
		]
		latest = rows[-1]
		snapshots.append(
			{
				"timestep": timestep,
				"phase": latest["phase"],
				"battery_min": min(battery_values),
				"battery_max": max(battery_values),
				"battery_avg": float(np.mean(battery_values)),
				"battery_last": latest["battery_level"],
				"reaction_time_ms": float(np.mean(reaction_samples)) if reaction_samples else None,
				"transition_count": len(rows),
			}
		)

	return snapshots


def build_phase_stats(
	phases: list[str],
	solar_rows: list[dict],
	transition_rows: list[dict],
	snapshots: list[dict],
) -> dict[str, dict]:
	"""Aggregate phase-level metrics using realistic counting rules."""
	phase_stats = {
		phase_name: {
			"avg_battery": 0.0,
			"total_grid_energy": 0.0,
			"safety_violations": 0,
			"avg_reaction_time": 0.0,
		}
		for phase_name in phases
	}

	for phase_name in phases:
		phase_solar = [row for row in solar_rows if row["phase"] == phase_name]
		phase_transitions = [row for row in transition_rows if row["phase"] == phase_name]
		phase_snapshots = [row for row in snapshots if row["phase"] == phase_name]
		phase_reaction_samples = [
			row["reaction_time_ms"]
			for row in phase_transitions
			if row["reaction_time_ms"] is not None
		]

		phase_stats[phase_name]["avg_battery"] = (
			float(np.mean([row["battery_avg"] for row in phase_snapshots]))
			if phase_snapshots
			else 0.0
		)
		phase_stats[phase_name]["total_grid_energy"] = sum(row["grid_energy"] for row in phase_solar) + sum(
			row["grid_energy"] for row in phase_transitions
		)
		phase_stats[phase_name]["avg_reaction_time"] = (
			float(np.mean(phase_reaction_samples)) if phase_reaction_samples else 0.0
		)

	# Count safety violations as safe->unsafe edges (same semantics as logger summary).
	ordered_transitions = sorted(
		transition_rows,
		key=lambda row: (row["timestep"], row["row_index"]),
	)
	unsafe_active = False
	for row in ordered_transitions:
		unsafe_now = bool(row["safety_violation"])
		if unsafe_now and not unsafe_active:
			phase_name = row["phase"]
			if phase_name in phase_stats:
				phase_stats[phase_name]["safety_violations"] += 1
		unsafe_active = unsafe_now

	return phase_stats


def plot_stress_test_dashboard(
	csv_path: Path,
	output_path: Path,
	*,
	display_limit: int | None = 300,
) -> None:
	"""Generate a comprehensive stress test evaluation dashboard."""
	data = load_evaluation_data(csv_path)
	if not data["solar_cycles"] and not data["state_transitions"]:
		raise ValueError("No evaluation rows found in evaluation CSV.")

	solar_rows = data["solar_cycles"]
	transition_rows = data["state_transitions"]
	snapshots = build_timestep_snapshots(transition_rows)

	# Extract unique timestep entries.
	timesteps = sorted(set([row["timestep"] for row in solar_rows] + [row["timestep"] for row in snapshots]))
	if not timesteps:
		raise ValueError("No valid timestep data found.")

	phase_by_ts: dict[int, str] = {}
	for row in solar_rows:
		phase_by_ts[row["timestep"]] = row["phase"]
	for row in snapshots:
		phase_by_ts.setdefault(row["timestep"], row["phase"])

	def get_phase_name(ts: int) -> str:
		return phase_by_ts.get(ts, "ZERO_SUNLIGHT")

	# Aggregate metrics by phase.
	observed_phases = {get_phase_name(ts) for ts in timesteps}
	phase_order = ["HIGH_SUNLIGHT", "CLOUD_STRESS", "ZERO_SUNLIGHT"]
	extra_phases = sorted([phase for phase in observed_phases if phase not in phase_order])
	phases = [phase for phase in phase_order if phase in observed_phases] + extra_phases
	if not phases:
		phases = ["ZERO_SUNLIGHT"]

	phase_colors = {
		"HIGH_SUNLIGHT": "#FFD700",
		"CLOUD_STRESS": "#A9A9A9",
		"ZERO_SUNLIGHT": "#191970",
	}
	phase_stats = build_phase_stats(phases, solar_rows, transition_rows, snapshots)

	# Aggregate battery values per timestep for a more informative plot.
	sorted_ts = [row["timestep"] for row in snapshots]
	sorted_battery_min = [row["battery_min"] for row in snapshots]
	sorted_battery_max = [row["battery_max"] for row in snapshots]
	sorted_battery_avg = [row["battery_avg"] for row in snapshots]

	wattage_samples_by_ts: dict[int, list[float]] = defaultdict(list)
	for row in solar_rows:
		wattage_samples_by_ts[row["timestep"]].append(row["wattage"])
	sorted_wattage = [
		float(np.mean(wattage_samples_by_ts.get(ts, [0.0])))
		for ts in sorted_ts
	]

	# Keep chart readable on very long runs while preserving summary stats across full data.
	if display_limit is not None and display_limit > 0 and len(sorted_ts) > display_limit:
		sorted_ts = sorted_ts[-display_limit:]
		sorted_battery_min = sorted_battery_min[-display_limit:]
		sorted_battery_max = sorted_battery_max[-display_limit:]
		sorted_battery_avg = sorted_battery_avg[-display_limit:]
		sorted_wattage = sorted_wattage[-display_limit:]

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
	grid_energy_vals = [
		phase_stats[p].get("total_grid_energy", 0) for p in phases
	]
	colors_list = [phase_colors.get(p, "#4C72B0") for p in phases]
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
		"SHEM System Performance Dashboard",
		fontsize=14,
		fontweight="bold",
		y=0.98,
	)
	plt.savefig(output_path, dpi=150, bbox_inches="tight")
	plt.close()


def parse_args() -> argparse.Namespace:
	"""Parse plotting options for window size and input/output paths."""
	parser = argparse.ArgumentParser(description="Generate SHEM performance dashboard plots.")
	parser.add_argument(
		"--csv",
		default="evaluation_results.csv",
		help="Path to evaluation CSV input (default: evaluation_results.csv)",
	)
	parser.add_argument(
		"--output",
		default="battery_level_over_time.png",
		help="Output image path (default: battery_level_over_time.png)",
	)
	parser.add_argument(
		"--window",
		type=int,
		default=300,
		help="Number of latest timesteps to display in time-series charts (default: 300)",
	)
	parser.add_argument(
		"--full",
		action="store_true",
		help="Display all timesteps in time-series charts (ignores --window)",
	)
	return parser.parse_args()


def main() -> None:
	"""Read evaluation CSV and generate a configurable performance dashboard."""
	args = parse_args()
	csv_path = Path(args.csv)
	output_path = Path(args.output)
	display_limit = None if args.full else args.window

	if display_limit is not None and display_limit <= 0:
		raise ValueError("--window must be a positive integer when --full is not used.")

	if not csv_path.exists():
		raise FileNotFoundError(
			"evaluation_results.csv was not found. Run the stress test before plotting results."
		)

	plot_stress_test_dashboard(csv_path, output_path, display_limit=display_limit)
	print(f"Saved stress test dashboard to {output_path}")


if __name__ == "__main__":
	main()