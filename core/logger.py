"""Evaluation logging utilities for the SHEM stress test."""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import fmean
from typing import Any


class EvaluationLogger:
	"""Collects runtime metrics and writes evaluation rows to CSV."""

	FIELDNAMES = [
		"event_type",
		"timestep",
		"phase",
		"weather",
		"wattage",
		"solar_status",
		"from_state",
		"to_state",
		"battery_level",
		"battery_health",
		"reaction_time_ms",
		"grid_energy_saved_units",
		"safety_violation",
	]

	def __init__(self, csv_path: str = "evaluation_results.csv", safe_battery_threshold: int = 20):
		self.csv_path = Path(csv_path)
		self.safe_battery_threshold = safe_battery_threshold
		self.reaction_times_ms: list[float] = []
		self.total_grid_energy_saved = 0.0
		self.battery_safety_violations = 0
		self._last_battery_level: float | None = None
		self._unsafe_condition_active = False
		self._initialize_file()

	def _initialize_file(self) -> None:
		with self.csv_path.open("w", newline="", encoding="utf-8") as csv_file:
			writer = csv.DictWriter(csv_file, fieldnames=self.FIELDNAMES)
			writer.writeheader()

	def _append_row(self, row: dict[str, Any]) -> None:
		with self.csv_path.open("a", newline="", encoding="utf-8") as csv_file:
			writer = csv.DictWriter(csv_file, fieldnames=self.FIELDNAMES)
			writer.writerow(row)

	def log_solar_cycle(
		self,
		timestep: int,
		phase: str,
		weather: str,
		wattage: float,
		solar_status: str,
	) -> None:
		grid_energy_saved_units = min(wattage / 100.0, 8.0)
		self.total_grid_energy_saved += grid_energy_saved_units
		self._append_row(
			{
				"event_type": "solar_cycle",
				"timestep": timestep,
				"phase": phase,
				"weather": weather,
				"wattage": f"{wattage:.2f}",
				"solar_status": solar_status,
				"from_state": "",
				"to_state": "",
				"battery_level": "",
				"battery_health": "",
				"reaction_time_ms": "",
				"grid_energy_saved_units": f"{grid_energy_saved_units:.2f}",
				"safety_violation": 0,
			}
		)

	def log_state_transition(
		self,
		*,
		timestep: int,
		phase: str,
		weather: str,
		wattage: float,
		solar_status: str,
		from_state: str,
		to_state: str,
		battery_level: float,
		battery_health: str,
		reaction_time_ms: float | None = None,
	) -> None:
		battery_support_units = 0.0
		if self._last_battery_level is not None:
			battery_support_units = max(0.0, self._last_battery_level - battery_level)

		unsafe_condition = (
			battery_level < self.safe_battery_threshold or battery_health != "HEALTHY"
		)
		if unsafe_condition and not self._unsafe_condition_active:
			self.battery_safety_violations += 1
		self._unsafe_condition_active = unsafe_condition

		if reaction_time_ms is not None:
			self.reaction_times_ms.append(reaction_time_ms)

		self.total_grid_energy_saved += battery_support_units
		self._last_battery_level = battery_level

		self._append_row(
			{
				"event_type": "state_transition",
				"timestep": timestep,
				"phase": phase,
				"weather": weather,
				"wattage": f"{wattage:.2f}",
				"solar_status": solar_status,
				"from_state": from_state,
				"to_state": to_state,
				"battery_level": f"{battery_level:.2f}",
				"battery_health": battery_health,
				"reaction_time_ms": "" if reaction_time_ms is None else f"{reaction_time_ms:.2f}",
				"grid_energy_saved_units": f"{battery_support_units:.2f}",
				"safety_violation": int(unsafe_condition),
			}
		)

	def build_summary(self) -> dict[str, float]:
		average_reaction_time = fmean(self.reaction_times_ms) if self.reaction_times_ms else 0.0
		return {
			"total_grid_energy_saved": self.total_grid_energy_saved,
			"battery_safety_violations": float(self.battery_safety_violations),
			"average_reaction_time_ms": average_reaction_time,
		}