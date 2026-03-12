"""Solar agent module for the SHEM Multi-Agent System."""

import time

from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message


class SolarAgent(Agent):
	"""
	A Simple Reflex Agent that monitors solar energy generation.
    
	This agent implements the Sense-Think-Act cycle:
	- SENSE: Perceives wattage from the WeatherEnvironment
	- THINK: Evaluates conditions against a threshold (300W)
	- ACT: Logs the symbolic status ("LOW" or "OPTIMAL")
    
	The agent uses a PeriodicBehaviour to continuously monitor
	environmental conditions at regular intervals.
    
	Attributes:
		environment: Reference to the WeatherEnvironment to sense
	"""
    
	def __init__(
		self,
		jid,
		password,
		environment,
		manager_jid,
		evaluation_logger,
		verify_security=False,
	):
		"""
		Initialize the Solar Agent.
        
		Args:
			jid (str): Jabber ID for XMPP authentication
			password (str): Password for XMPP authentication
			environment: WeatherEnvironment instance to sense
			manager_jid (str): JID of the HomeManagerAgent to send status messages to
			verify_security (bool): Whether to verify SSL certificates
		"""
		super().__init__(jid, password, verify_security=verify_security)
		self.environment = environment
		self.manager_jid = manager_jid
		self.evaluation_logger = evaluation_logger
        
	async def setup(self):
		"""
		Setup method called when the agent starts.
        
		Registers the PeriodicBehaviour for continuous sensing.
		"""
		print(f"[SolarAgent] Agent {self.jid} starting up...")
        
		# Register the periodic sensing behavior (every 3 seconds)
		sense_behaviour = self.SenseSunlight(
			period=3,
			environment=self.environment,
			manager_jid=self.manager_jid,
			evaluation_logger=self.evaluation_logger,
		)
		self.add_behaviour(sense_behaviour)
        
		print(f"[SolarAgent] Sensing behavior registered with 3-second period")
    
    
	class SenseSunlight(PeriodicBehaviour):
		"""
		Periodic Behaviour that implements the Sense-Think-Act cycle.
        
		This behaviour runs every 3 seconds to:
		1. SENSE: Sample the environment for current wattage
		2. THINK: Classify the wattage as LOW or OPTIMAL
		3. ACT: Log the status for monitoring
        
		Attributes:
			environment: Reference to the WeatherEnvironment
		"""
        
		def __init__(self, period, environment, manager_jid, evaluation_logger):
			"""
			Initialize the sensing behaviour.
            
			Args:
				period (float): Time in seconds between executions
				environment: WeatherEnvironment instance to sense
				manager_jid (str): JID of the HomeManagerAgent to INFORM
			"""
			super().__init__(period=period)
			self.environment = environment
			self.manager_jid = manager_jid
			self.evaluation_logger = evaluation_logger
			self.sense_count = 0
            
		async def run(self):
			"""
			Execute the Sense-Think-Act cycle.
            
			This method is called periodically by the SPADE framework.
			It implements a Simple Reflex Agent that maps percepts
			directly to actions based on condition-action rules.
			"""
			self.sense_count += 1
            
			# ═══════════════════════════════════════════════════════
			# SENSE: Perceive the environment
			# ═══════════════════════════════════════════════════════
			if self.environment.is_complete():
				self.kill(exit_code=0)
				return

			environment_state = self.environment.update_weather()
			wattage = environment_state["wattage"]
			weather_status = environment_state["weather"]
			timestep = environment_state["timestep"]
			phase = environment_state["phase"]
            
			# ═══════════════════════════════════════════════════════
			# THINK: Evaluate percepts and apply condition-action rules
			# ═══════════════════════════════════════════════════════
			# Simple Reflex Agent Rule:
			# IF wattage < 300 THEN status = "LOW"
			# ELSE status = "OPTIMAL"
			if wattage < 300:
				status = "LOW"
			else:
				status = "OPTIMAL"

			self.evaluation_logger.log_solar_cycle(
				timestep=timestep,
				phase=phase,
				weather=weather_status,
				wattage=wattage,
				solar_status=status,
			)
            
			# ═══════════════════════════════════════════════════════
			# ACT: Log status and send FIPA-ACL INFORM to Manager
			# ═══════════════════════════════════════════════════════
			print(f"\n[Sense #{self.sense_count}] Solar Agent Perception:")
			print(f"  Weather: {weather_status}")
			print(f"  Wattage: {wattage:.2f}W")
			print(f"  Status:  {status}")

			# Compose and send a FIPA-ACL INFORM message to the Manager
			msg = Message(to=str(self.manager_jid))
			msg.sender = str(self.agent.jid)
			msg.set_metadata("performative", "inform")
			msg.set_metadata("timestep", str(timestep))
			msg.set_metadata("phase", phase)
			msg.set_metadata("weather", weather_status)
			msg.set_metadata("wattage", f"{wattage:.2f}")
			msg.set_metadata("sent_at", f"{time.perf_counter():.9f}")
			msg.body = status
			await self.send(msg)
			print(f"  [SolarAgent] >> INFORM sent to {self.manager_jid}: '{status}'")
			print("-" * 50)
