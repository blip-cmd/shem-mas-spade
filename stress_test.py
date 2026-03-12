"""Day 6 bounded stress-test scenario for the SHEM Multi-Agent System."""

import asyncio
from core.environment import WeatherEnvironment
from core.logger import EvaluationLogger
from agents.solar_agent import SolarAgent
from agents.manager_agent import HomeManagerAgent


SOLAR_AGENT_JID = "solar_sensor@localhost"
SOLAR_AGENT_PASSWORD = "sensor123"
MANAGER_AGENT_JID = "home_manager@localhost"
MANAGER_AGENT_PASSWORD = "manager123"


async def run_stress_test():
	"""
	Run the finite 25-step Day/Night stress scenario and print evaluation metrics.

	Stress profile:
	  T=0-10   HIGH_SUNLIGHT  — clear sky, 900-1200 W
	  T=11-15  CLOUD_STRESS   — 80% cloud probability, 80-220 W when cloudy
	  T=16-24  ZERO_SUNLIGHT  — night, 0 W
	"""
	print("=" * 60)
	print("SHEM - Smart Home Energy Manager")
	print("Day 6: System Evaluation Stress Test")
	print("=" * 60)
	print()

	evaluation_logger = EvaluationLogger(csv_path="evaluation_results.csv")

	# ═══════════════════════════════════════════════════════════════
	# Step 1: Scripted day/night environment (25 steps, 80% cloud stress)
	# ═══════════════════════════════════════════════════════════════
	print("[System] Initializing Weather Environment...")
	weather_env = WeatherEnvironment(cloudy_probability=0.8, total_steps=25)
	print("[System] Weather Environment initialized")
	print("[System] Stress profile: T=0-10 high sunlight | T=11-15 cloud stress | T=16-24 night")
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
	print("System is running the 25-step stress test.")
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


if __name__ == "__main__":
	try:
		asyncio.run(run_stress_test())
	except KeyboardInterrupt:
		print("\n[System] Exiting...")