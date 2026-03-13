"""Main entry point for the SHEM Multi-Agent System."""

import asyncio
import os
from pathlib import Path
from core.environment import WeatherEnvironment
from core.logger import EvaluationLogger
from agents.solar_agent import SolarAgent
from agents.manager_agent import HomeManagerAgent


def load_env_file(env_path):
	if not env_path.exists():
		return

	for raw_line in env_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue

		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")
		if key and key not in os.environ:
			os.environ[key] = value


load_env_file(Path(__file__).resolve().parent / ".env")


# XMPP Configuration for SPADE
# Note: For local testing, ensure an XMPP server is running (e.g., prosody, ejabberd)
XMPP_DOMAIN = os.getenv("XMPP_DOMAIN", "localhost")
SOLAR_AGENT_JID = os.getenv("SOLAR_AGENT_JID", f"solar_sensor@{XMPP_DOMAIN}")
SOLAR_AGENT_PASSWORD = os.getenv("SOLAR_AGENT_PASSWORD", "sensor123")
MANAGER_AGENT_JID = os.getenv("MANAGER_AGENT_JID", f"home_manager@{XMPP_DOMAIN}")
MANAGER_AGENT_PASSWORD = os.getenv("MANAGER_AGENT_PASSWORD", "manager123")


async def main():
	"""
	Bootstrap the SHEM MAS and run the open-ended simulation.

	The system runs continuously until interrupted with Ctrl+C.
	Use stress_test.py for the bounded Day 6 evaluation scenario.
	"""
	print("=" * 60)
	print("SHEM - Smart Home Energy Manager")
	print("Multi-Agent System")
	print("=" * 60)
	print()

	evaluation_logger = EvaluationLogger(csv_path="evaluation_results.csv")

	# ═══════════════════════════════════════════════════════════════
	# Step 1: Initialize the Stochastic Environment
	# ═══════════════════════════════════════════════════════════════
	print("[System] Initializing Weather Environment...")
	# Use stochastic behavior with no step limit for open-ended simulation
	weather_env = WeatherEnvironment(cloudy_probability=0.2, total_steps=None)
	print("[System] Weather Environment initialized")
	print(f"[System] Cloudy probability: {weather_env.cloudy_probability * 100:.0f}%")
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
	print("System is running. Press Ctrl+C to stop.")
	print("=" * 60)
	print()

	try:
		# ═══════════════════════════════════════════════════════════
		# Step 3: Run indefinitely — let agents drive the loop
		# ═══════════════════════════════════════════════════════════
		while solar_agent.is_alive() and manager_agent.is_alive():
			await asyncio.sleep(1)

	except KeyboardInterrupt:
		print("\n")
		print("=" * 60)
		print("[System] Shutdown signal received")
		print("[System] Stopping Solar Agent...")
		print("[System] Stopping Home Manager Agent...")

	finally:
		# ═══════════════════════════════════════════════════════════
		# Step 4: Graceful shutdown and session summary
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
		asyncio.run(main())
	except KeyboardInterrupt:
		print("\n[System] Exiting...")
