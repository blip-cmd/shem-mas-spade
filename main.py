"""
SHEM (Smart Home Energy Manager) Multi-Agent System
Main Entry Point

This is Day 3 of the SHEM project following the Prometheus methodology.
Focus: Lab 3 - Reactive Behavior

This module bootstraps the system by:
1. Creating a stochastic environment (WeatherEnvironment)
2. Spawning a Simple Reflex Agent (SolarAgent)
3. Spawning a Model-Based Agent (HomeManagerAgent)
4. Managing the agent lifecycle with graceful shutdown
"""

import asyncio
from core.environment import WeatherEnvironment
from agents.solar_agent import SolarAgent
from agents.manager_agent import HomeManagerAgent


# XMPP Configuration for SPADE
# Note: For local testing, ensure an XMPP server is running (e.g., prosody, ejabberd)
SOLAR_AGENT_JID = "solar_sensor@localhost"
SOLAR_AGENT_PASSWORD = "sensor123"
MANAGER_AGENT_JID = "home_manager@localhost"
MANAGER_AGENT_PASSWORD = "manager123"


async def main():
	"""
	Main entry point for the SHEM Multi-Agent System.
    
	Implements the system bootstrap process:
	1. Initialize the stochastic environment
	2. Create and start the Solar Agent
	3. Create and start the Home Manager Agent
	4. Run the simulation
	5. Handle graceful shutdown on interruption
	"""
	print("=" * 60)
	print("SHEM - Smart Home Energy Manager")
	print("Day 3: Reactive Behavior with Model-Based Agent")
	print("=" * 60)
	print()
    
	# ═══════════════════════════════════════════════════════════════
	# Step 1: Initialize the Stochastic Environment
	# ═══════════════════════════════════════════════════════════════
	print("[System] Initializing Weather Environment...")
	# Create environment with 20% probability of cloudy conditions
	weather_env = WeatherEnvironment(cloudy_probability=0.2)
	print("[System] Weather Environment initialized")
	print(f"[System] Cloudy probability: {weather_env.cloudy_probability * 100}%")
	print()
    
	# ═══════════════════════════════════════════════════════════════
	# Step 2: Create and Start the Agents
	# ═══════════════════════════════════════════════════════════════
	print("[System] Creating Solar Agent...")
	solar_agent = SolarAgent(
		jid=SOLAR_AGENT_JID,
		password=SOLAR_AGENT_PASSWORD,
		environment=weather_env,
		verify_security=False  # Disable SSL verification for local testing
	)
    
	print("[System] Starting Solar Agent...")
	await solar_agent.start(auto_register=True)
	print("[System] Solar Agent is now active")

	print("[System] Creating Home Manager Agent...")
	manager_agent = HomeManagerAgent(
		jid=MANAGER_AGENT_JID,
		password=MANAGER_AGENT_PASSWORD,
		verify_security=False  # Disable SSL verification for local testing
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
		# Step 3: Run the simulation
		# ═══════════════════════════════════════════════════════════
		# Keep the system running and let the agent's periodic behavior execute
		while solar_agent.is_alive() and manager_agent.is_alive():
			await asyncio.sleep(1)
            
	except KeyboardInterrupt:
		# ═══════════════════════════════════════════════════════════
		# Step 4: Graceful Shutdown Handler
		# ═══════════════════════════════════════════════════════════
		print("\n")
		print("=" * 60)
		print("[System] Shutdown signal received")
		print("[System] Stopping Solar Agent...")
		print("[System] Stopping Home Manager Agent...")
        
	finally:
		# Ensure agents are properly stopped
		await solar_agent.stop()
		await manager_agent.stop()
		print("[System] Solar Agent stopped")
		print("[System] Home Manager Agent stopped")
		print("[System] SHEM system shutdown complete")
		print("=" * 60)


if __name__ == "__main__":
	"""
	Entry point when running the script directly.
    
	Uses asyncio to run the async main function, which is required
	for SPADE agents that use async/await patterns.
	"""
	try:
		# Run the async main function
		asyncio.run(main())
	except KeyboardInterrupt:
		# Handle interrupt at the top level
		print("\n[System] Exiting...")
