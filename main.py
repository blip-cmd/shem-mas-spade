"""
SHEM (Smart Home Energy Manager) Multi-Agent System
Main Entry Point

This is Day 2 of the SHEM project following the Prometheus methodology.
Focus: Lab 2 - Perception and Environment Modeling

This module bootstraps the system by:
1. Creating a stochastic environment (WeatherEnvironment)
2. Spawning a Simple Reflex Agent (SolarAgent)
3. Managing the agent lifecycle with graceful shutdown
"""

import asyncio
import time
from core.environment import WeatherEnvironment
from agents.solar_agent import SolarAgent


# XMPP Configuration for SPADE
# Note: For local testing, ensure an XMPP server is running (e.g., prosody, ejabberd)
SOLAR_AGENT_JID = "solar_sensor@localhost"
SOLAR_AGENT_PASSWORD = "sensor123"


async def main():
	"""
	Main entry point for the SHEM Multi-Agent System.
    
	Implements the system bootstrap process:
	1. Initialize the stochastic environment
	2. Create and start the Solar Agent
	3. Run the simulation
	4. Handle graceful shutdown on interruption
	"""
	print("=" * 60)
	print("SHEM - Smart Home Energy Manager")
	print("Day 2: Perception and Environment Modeling")
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
	# Step 2: Create and Start the Solar Agent
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
		while solar_agent.is_alive():
			await asyncio.sleep(1)
            
	except KeyboardInterrupt:
		# ═══════════════════════════════════════════════════════════
		# Step 4: Graceful Shutdown Handler
		# ═══════════════════════════════════════════════════════════
		print("\n")
		print("=" * 60)
		print("[System] Shutdown signal received")
		print("[System] Stopping Solar Agent...")
        
	finally:
		# Ensure agents are properly stopped
		await solar_agent.stop()
		print("[System] Solar Agent stopped")
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
