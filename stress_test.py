"""Day 6 bounded stress-test scenario for the SHEM Multi-Agent System."""

import asyncio
import argparse
from core.environment import WeatherEnvironment
from core.logger import EvaluationLogger
from agents.solar_agent import SolarAgent
from agents.manager_agent import HomeManagerAgent


SOLAR_AGENT_JID = "solar_sensor@localhost"
SOLAR_AGENT_PASSWORD = "sensor123"
MANAGER_AGENT_JID = "home_manager@localhost"
MANAGER_AGENT_PASSWORD = "manager123"


async def run_stress_test(
	total_steps: int = 25,
	cloudy_probability: float = 0.8,
	high_sunlight_duration: int = 10,
	cloud_stress_duration: int = 5,
):
	"""
	Run the bounded Day/Night stress scenario and print evaluation metrics.

	Stress profile:
	  T=0-(high_sunlight_duration-1)            HIGH_SUNLIGHT   — clear sky, 900-1200 W
	  T=high_sunlight_duration-(+cloud_stress)  CLOUD_STRESS    — configurable cloud probability
	  remaining timesteps                       ZERO_SUNLIGHT   — night, 0 W
	"""
	if total_steps <= 0:
		raise ValueError("total_steps must be a positive integer")
	if not 0.0 <= cloudy_probability <= 1.0:
		raise ValueError("cloudy_probability must be between 0.0 and 1.0")
	if high_sunlight_duration < 0:
		raise ValueError("high_sunlight_duration must be >= 0")
	if cloud_stress_duration < 0:
		raise ValueError("cloud_stress_duration must be >= 0")

	high_sunlight_end = high_sunlight_duration - 1
	cloud_stress_end = high_sunlight_end + cloud_stress_duration
	night_start = cloud_stress_end + 1

	print("=" * 60)
	print("SHEM - Smart Home Energy Manager")
	print("Day 6: System Evaluation Stress Test")
	print("=" * 60)
	print()

	evaluation_logger = EvaluationLogger(csv_path="evaluation_results.csv")

	# ═══════════════════════════════════════════════════════════════
	# Step 1: Scripted day/night environment
	# ═══════════════════════════════════════════════════════════════
	print("[System] Initializing Weather Environment...")
	weather_env = WeatherEnvironment(
		cloudy_probability=cloudy_probability,
		total_steps=total_steps,
		high_sunlight_end=high_sunlight_end,
		cloud_stress_end=cloud_stress_end,
	)
	print("[System] Weather Environment initialized")
	print(
		"[System] Stress profile: "
		f"T=0-{high_sunlight_end} high sunlight | "
		f"T={high_sunlight_end + 1}-{cloud_stress_end} cloud stress | "
		f"T={night_start}+ night"
	)
	print(
		f"[System] Config: total_steps={total_steps}, "
		f"high_sunlight_duration={high_sunlight_duration}, "
		f"cloud_stress_duration={cloud_stress_duration}, "
		f"cloudy_probability={cloudy_probability:.2f}"
	)
	print()

	# ═══════════════════════════════════════════════════════════════
	# Step 2: Create and Start the Agents
	# ═══════════════════════════════════════════════════════════════
	print("[System] Creating Solar Agent...")
	solar_agent = SolarAgent(
		jid=SOLAR_AGENT_JID,
		password=SOLAR_AGENT_PASSWORD,
		environment=weather_env,
		manager_jid=MANAGER_AGENT_JID,
		evaluation_logger=evaluation_logger,
		verify_security=False,
	)

	print("[System] Starting Solar Agent...")
	await solar_agent.start(auto_register=True)
	print("[System] Solar Agent is now active")

	print("[System] Creating Home Manager Agent...")
	manager_agent = HomeManagerAgent(
		jid=MANAGER_AGENT_JID,
		password=MANAGER_AGENT_PASSWORD,
		solar_jid=SOLAR_AGENT_JID,
		evaluation_logger=evaluation_logger,
		verify_security=False,
	)

	print("[System] Starting Home Manager Agent...")
	await manager_agent.start(auto_register=True)
	print("[System] Home Manager Agent is now active")
	print()

	print("=" * 60)
	print(f"System is running the {total_steps}-step stress test.")
	print("=" * 60)
	print()

	try:
		# ═══════════════════════════════════════════════════════════
		# Step 3: Run until all 25 environment steps are consumed
		# ═══════════════════════════════════════════════════════════
		while solar_agent.is_alive() and manager_agent.is_alive() and not weather_env.is_complete():
			await asyncio.sleep(1)

		if weather_env.is_complete() and solar_agent.is_alive() and manager_agent.is_alive():
			print("[System] Stress scenario complete. Waiting for final manager reaction...")
			await asyncio.sleep(5)

	except KeyboardInterrupt:
		print("\n")
		print("=" * 60)
		print("[System] Shutdown signal received")
		print("[System] Stopping Solar Agent...")
		print("[System] Stopping Home Manager Agent...")

	finally:
		# ═══════════════════════════════════════════════════════════
		# Step 4: Graceful shutdown and evaluation summary
		# ═══════════════════════════════════════════════════════════
		await solar_agent.stop()
		await manager_agent.stop()
		summary = evaluation_logger.build_summary()
		print("[System] Solar Agent stopped")
		print("[System] Home Manager Agent stopped")
		print()
		print(f"Total Grid Energy Saved: {summary['total_grid_energy_saved']:.2f} units")
		print(f"Battery Safety Violations: {int(summary['battery_safety_violations'])} times")
		print(f"Average Reaction Time: {summary['average_reaction_time_ms']:.2f} ms")
		print("[System] Detailed results written to evaluation_results.csv")
		print("[System] SHEM system shutdown complete")
		print("=" * 60)


def parse_args() -> argparse.Namespace:
	"""Parse command-line args for stress test configuration."""
	parser = argparse.ArgumentParser(description="Run the SHEM bounded stress test.")
	parser.add_argument(
		"--steps",
		type=int,
		default=25,
		help="Total number of stress-test steps (default: 25)",
	)
	parser.add_argument(
		"--high-sunlight-duration",
		type=int,
		default=10,
		help="Number of HIGH_SUNLIGHT timesteps (default: 10)",
	)
	parser.add_argument(
		"--cloud-stress-duration",
		type=int,
		default=5,
		help="Number of CLOUD_STRESS timesteps after high-sunlight phase (default: 5)",
	)
	parser.add_argument(
		"--cloudy-probability",
		type=float,
		default=0.8,
		help="Cloudy probability used by WeatherEnvironment (0.0 to 1.0, default: 0.8)",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = parse_args()
	try:
		asyncio.run(
			run_stress_test(
				total_steps=args.steps,
				cloudy_probability=args.cloudy_probability,
				high_sunlight_duration=args.high_sunlight_duration,
				cloud_stress_duration=args.cloud_stress_duration,
			)
		)
	except KeyboardInterrupt:
		print("\n[System] Exiting...")