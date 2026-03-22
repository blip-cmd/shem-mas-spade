"""Home manager agent module for the SHEM Multi-Agent System."""

import asyncio
import random
import time

from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, FSMBehaviour, State
from spade.template import Template

try:
	import spade.df as spade_df
except ImportError:
	spade_df = None


class BatteryManagementCapability(FSMBehaviour):
	"""Handles state transitions for battery management decisions."""

	async def on_start(self):
		print("[Manager] Initializing Battery Management FSM...")

	async def on_end(self):
		print("[Manager] FSM Terminated.")


class EnergyMonitoringCapability(CyclicBehaviour):
	"""Receives INFORM messages and updates the agent's internal beliefs."""

	async def run(self):
		msg = await self.receive(timeout=10)
		if msg:
			self.agent.update_beliefs_from_message(msg)
			reaction_time_ms = self.agent.reaction_time_ms(msg)
			self.agent.last_reaction_time_ms = reaction_time_ms
			print(f"  [HomeManagerAgent] << INFORM received from {msg.sender}: '{msg.body}'")
		else:
			print("[Manager] WARNING: Communication Timeout! Reverting to Safe Mode.")
			self.agent.current_solar_belief = "UNKNOWN"
			self.agent.solar_status = "UNKNOWN"


class FailureAwareState(State):
	def maybe_handle_battery_failure(self, current_state):
		"""Simulate a critical battery overheat with 5% probability."""
		if self.agent.battery_health == "OVERHEATED":
			self.transition(current_state, self.agent.EMERGENCY)
			return True

		if random.random() < 0.05:
			self.agent.battery_health = "OVERHEATED"
			print(
				"[HomeManagerAgent] CRITICAL: Battery overheats. "
				"Dropping all plans and entering EMERGENCY state."
			)
			self.transition(current_state, self.agent.EMERGENCY)
			return True

		return False

	def transition(self, current_state, next_state, reaction_time_ms=None):
		"""Record a transition row and move the FSM to the next state."""
		if reaction_time_ms is None:
			reaction_time_ms = self.agent.consume_reaction_time()

		self.agent.evaluation_logger.log_state_transition(
			timestep=self.agent.current_timestep,
			phase=self.agent.current_phase,
			weather=self.agent.current_weather,
			wattage=self.agent.current_wattage,
			solar_status=self.agent.current_solar_belief,
			from_state=current_state,
			to_state=next_state,
			battery_level=self.agent.battery_level,
			battery_health=self.agent.battery_health,
			reaction_time_ms=reaction_time_ms,
		)
		self.set_next_state(next_state)


class IdleState(FailureAwareState):
	async def run(self):
		if self.maybe_handle_battery_failure(self.agent.IDLE):
			return

		await asyncio.sleep(1)

		solar_status = self.agent.current_solar_belief

		self.agent.battery_level = max(0, self.agent.battery_level - 2)

		intention = "Monitor environment and preserve energy"
		print(
			f"[HomeManagerAgent] State=IDLE | Battery={self.agent.battery_level}% "
			f"| Solar={solar_status} | Intention={intention}"
		)

		if self.agent.battery_level < 20:
			self.transition(self.agent.IDLE, self.agent.EMERGENCY)
		elif solar_status == "UNKNOWN":
			self.transition(self.agent.IDLE, self.agent.SYSTEM_CHECK)
		elif solar_status == "OPTIMAL" and self.agent.battery_level < 90:
			self.transition(self.agent.IDLE, self.agent.CHARGING)
		else:
			self.transition(self.agent.IDLE, self.agent.IDLE)


class ChargingState(FailureAwareState):
	async def run(self):
		if self.maybe_handle_battery_failure(self.agent.CHARGING):
			return

		await asyncio.sleep(3)

		if self.maybe_handle_battery_failure(self.agent.CHARGING):
			return

		self.agent.battery_level = min(100, self.agent.battery_level + 5)

		intention = "Maximize battery charge while solar is available"
		print(
			f"[HomeManagerAgent] State=CHARGING | Battery={self.agent.battery_level}% "
			f"| Solar={self.agent.current_solar_belief} | Intention={intention}"
		)

		if self.agent.battery_level < 20:
			self.transition(self.agent.CHARGING, self.agent.EMERGENCY)
		elif self.agent.current_solar_belief == "UNKNOWN":
			self.transition(self.agent.CHARGING, self.agent.SYSTEM_CHECK)
		elif self.agent.current_solar_belief != "OPTIMAL" or self.agent.battery_level >= 90:
			self.transition(self.agent.CHARGING, self.agent.IDLE)
		else:
			self.transition(self.agent.CHARGING, self.agent.CHARGING)


class SystemCheckState(FailureAwareState):
	async def run(self):
		print(
			"[HomeManagerAgent] WARNING: Communication Lost. "
			"Reverting to Safe Mode (Internal Model only)."
		)

		await asyncio.sleep(1)

		if self.maybe_handle_battery_failure(self.agent.SYSTEM_CHECK):
			return

		self.agent.battery_level = max(0, self.agent.battery_level - 2)

		intention = "Fallback monitoring with stale beliefs only"
		print(
			f"[HomeManagerAgent] State=SYSTEM_CHECK | Battery={self.agent.battery_level}% "
			f"| BatteryHealth={self.agent.battery_health} | Solar={self.agent.current_solar_belief} "
			f"| Intention={intention}"
		)

		if self.agent.battery_level < 20:
			self.transition(self.agent.SYSTEM_CHECK, self.agent.EMERGENCY)
		elif self.agent.current_solar_belief == "OPTIMAL" and self.agent.battery_level < 90:
			self.transition(self.agent.SYSTEM_CHECK, self.agent.CHARGING)
		elif self.agent.current_solar_belief in {"LOW", "OPTIMAL"}:
			self.transition(self.agent.SYSTEM_CHECK, self.agent.IDLE)
		else:
			self.transition(self.agent.SYSTEM_CHECK, self.agent.SYSTEM_CHECK)


class EmergencyState(FailureAwareState):
	async def run(self):
		if self.maybe_handle_battery_failure(self.agent.EMERGENCY):
			return

		await asyncio.sleep(1)

		solar_status = self.agent.current_solar_belief

		self.agent.battery_level = max(0, self.agent.battery_level - 1)

		intention = "Preserve critical battery and restore safe level"
		print(
			f"[HomeManagerAgent] State=EMERGENCY | Battery={self.agent.battery_level}% "
			f"| BatteryHealth={self.agent.battery_health} | Solar={solar_status} "
			f"| Intention={intention}"
		)

		if self.agent.battery_health == "OVERHEATED":
			self.transition(self.agent.EMERGENCY, self.agent.EMERGENCY)
		elif solar_status == "OPTIMAL":
			self.transition(self.agent.EMERGENCY, self.agent.CHARGING)
		else:
			self.transition(self.agent.EMERGENCY, self.agent.EMERGENCY)


class HomeManagerAgent(Agent):
	"""
	A Model-Based Agent that manages home battery behavior.

	The agent tracks battery level as its internal model and transitions
	between IDLE, CHARGING, SYSTEM_CHECK, and EMERGENCY states according to
	maintenance, charging, and fault-handling goals.
	"""

	IDLE = "IDLE"
	CHARGING = "CHARGING"
	SYSTEM_CHECK = "SYSTEM_CHECK"
	EMERGENCY = "EMERGENCY"

	def __init__(self, jid, password, solar_jid, evaluation_logger, verify_security=False):
		"""Initialize beliefs, runtime metrics, and logger hooks for evaluation."""
		super().__init__(jid, password, verify_security=verify_security)
		self.solar_jid = solar_jid
		self.evaluation_logger = evaluation_logger
		self.battery_level = 50
		self.current_solar_belief = "UNKNOWN"
		self.solar_status = "UNKNOWN"
		self.battery_health = "HEALTHY"
		self.current_timestep = -1
		self.current_phase = "BOOT"
		self.current_weather = "Unknown"
		self.current_wattage = 0.0
		self.last_reaction_time_ms = None

	def update_beliefs_from_message(self, msg):
		"""Update internal beliefs from a weather-monitoring INFORM message."""
		self.current_solar_belief = msg.body
		self.solar_status = msg.body
		self.current_timestep = int(msg.get_metadata("timestep") or self.current_timestep)
		self.current_phase = msg.get_metadata("phase") or self.current_phase
		self.current_weather = msg.get_metadata("weather") or self.current_weather
		self.current_wattage = float(msg.get_metadata("wattage") or self.current_wattage)

	def reaction_time_ms(self, msg):
		"""Compute transport delay from sender metadata timestamp to now."""
		sent_at = msg.get_metadata("sent_at")
		if sent_at is None:
			return None
		return (time.perf_counter() - float(sent_at)) * 1000

	def consume_reaction_time(self):
		"""Consume and clear the latest measured reaction time for one transition."""
		reaction_time_ms = self.last_reaction_time_ms
		self.last_reaction_time_ms = None
		return reaction_time_ms

	async def setup(self):
		print(f"[HomeManagerAgent] Agent {self.jid} starting up...")
		print("[Manager] Searching DF for Weather Services...")
		if spade_df is not None and hasattr(self, "client") and hasattr(self.client, "get_services"):
			try:
				results = await self.client.get_services(service_type="weather-monitoring")
				if results:
					provider = getattr(results[0], "jid", "unknown")
					print(f"[Manager] Found Weather Service Provider: {provider}")
				else:
					print("[Manager] No Weather Service found.")
			except Exception as error:
				print(f"[Manager] DF Search Failed: {error}")
		else:
			print("[Manager] DF search API unavailable on this SPADE version.")

		comm_template = Template()
		comm_template.set_metadata("performative", "inform")
		comm_template.set_metadata("ontology", "weather-monitoring")
		self.add_behaviour(EnergyMonitoringCapability(), comm_template)
		print("[HomeManagerAgent] EnergyMonitoringCapability registered")

		fsm = BatteryManagementCapability()
		fsm.add_state(name=self.IDLE, state=IdleState(), initial=True)
		fsm.add_state(name=self.CHARGING, state=ChargingState())
		fsm.add_state(name=self.SYSTEM_CHECK, state=SystemCheckState())
		fsm.add_state(name=self.EMERGENCY, state=EmergencyState())

		# Register all legal transitions among operational states.
		fsm.add_transition(source=self.IDLE, dest=self.IDLE)
		fsm.add_transition(source=self.IDLE, dest=self.CHARGING)
		fsm.add_transition(source=self.IDLE, dest=self.SYSTEM_CHECK)
		fsm.add_transition(source=self.IDLE, dest=self.EMERGENCY)
		fsm.add_transition(source=self.CHARGING, dest=self.CHARGING)
		fsm.add_transition(source=self.CHARGING, dest=self.IDLE)
		fsm.add_transition(source=self.CHARGING, dest=self.SYSTEM_CHECK)
		fsm.add_transition(source=self.CHARGING, dest=self.EMERGENCY)
		fsm.add_transition(source=self.SYSTEM_CHECK, dest=self.SYSTEM_CHECK)
		fsm.add_transition(source=self.SYSTEM_CHECK, dest=self.IDLE)
		fsm.add_transition(source=self.SYSTEM_CHECK, dest=self.CHARGING)
		fsm.add_transition(source=self.SYSTEM_CHECK, dest=self.EMERGENCY)
		fsm.add_transition(source=self.EMERGENCY, dest=self.EMERGENCY)
		fsm.add_transition(source=self.EMERGENCY, dest=self.SYSTEM_CHECK)
		fsm.add_transition(source=self.EMERGENCY, dest=self.CHARGING)
		fsm.add_transition(source=self.EMERGENCY, dest=self.IDLE)

		self.add_behaviour(fsm)
		print("[HomeManagerAgent] BatteryManagementCapability registered")