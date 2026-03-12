"""
Home Manager Agent Module for SHEM Multi-Agent System

This module implements a Model-Based Agent using a Finite State Machine (FSM)
to maintain internal state (battery level, solar belief, battery health)
and react to changing conditions.
"""

import asyncio
import random

from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.template import Template


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

	def __init__(self, jid, password, solar_jid, verify_security=False):
		super().__init__(jid, password, verify_security=verify_security)
		self.solar_jid = solar_jid
		self.battery_level = 50
		# Belief: last known solar status received from SolarAgent
		self.solar_status = "LOW"
		self.battery_health = "HEALTHY"

	async def setup(self):
		print(f"[HomeManagerAgent] Agent {self.jid} starting up...")

		fsm = self.BatteryFSM()
		fsm.add_state(name=self.IDLE, state=self.IdleState(), initial=True)
		fsm.add_state(name=self.CHARGING, state=self.ChargingState())
		fsm.add_state(name=self.SYSTEM_CHECK, state=self.SystemCheckState())
		fsm.add_state(name=self.EMERGENCY, state=self.EmergencyState())

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

		# Register the FSM with a Template so only FIPA-ACL INFORM messages
		# from the SolarAgent are routed into this behaviour's mailbox.
		inform_template = Template()
		inform_template.set_metadata("performative", "inform")

		self.add_behaviour(fsm, inform_template)
		print("[HomeManagerAgent] FSM behavior registered (listening for INFORM messages)")

	class BatteryFSM(FSMBehaviour):
		async def on_start(self):
			print("[HomeManagerAgent] FSM started")

	class FailureAwareState(State):
		def check_battery_health(self):
			"""Simulate a critical battery overheat with 5% probability."""
			if self.agent.battery_health == "OVERHEATED":
				return True

			if random.random() < 0.05:
				self.agent.battery_health = "OVERHEATED"
				print(
					"[HomeManagerAgent] CRITICAL: Battery overheats. "
					"Dropping all plans and entering EMERGENCY state."
				)
				return True

			return False

	class IdleState(FailureAwareState):
		async def run(self):
			if self.check_battery_health():
				self.set_next_state(self.agent.EMERGENCY)
				return

			# Wait up to 10 seconds for a real FIPA-ACL INFORM from the SolarAgent.
			msg = await self.receive(timeout=10)
			if msg is None:
				self.set_next_state(self.agent.SYSTEM_CHECK)
				return

			self.agent.solar_status = msg.body
			print(f"  [HomeManagerAgent] << INFORM received from {msg.sender}: '{msg.body}'")

			if self.check_battery_health():
				self.set_next_state(self.agent.EMERGENCY)
				return

			solar_status = self.agent.solar_status

			# In IDLE the battery slowly discharges due to household baseline usage.
			self.agent.battery_level = max(0, self.agent.battery_level - 2)

			intention = "Monitor environment and preserve energy"
			print(
				f"[HomeManagerAgent] State=IDLE | Battery={self.agent.battery_level}% "
				f"| Solar={solar_status} | Intention={intention}"
			)

			if self.agent.battery_level < 20:
				self.set_next_state(self.agent.EMERGENCY)
			elif solar_status == "OPTIMAL" and self.agent.battery_level < 90:
				self.set_next_state(self.agent.CHARGING)
			else:
				self.set_next_state(self.agent.IDLE)

	class ChargingState(FailureAwareState):
		async def run(self):
			if self.check_battery_health():
				self.set_next_state(self.agent.EMERGENCY)
				return

			await asyncio.sleep(3)

			if self.check_battery_health():
				self.set_next_state(self.agent.EMERGENCY)
				return

			# While charging, battery increases due to available solar generation.
			self.agent.battery_level = min(100, self.agent.battery_level + 5)

			intention = "Maximize battery charge while solar is available"
			print(
				f"[HomeManagerAgent] State=CHARGING | Battery={self.agent.battery_level}% "
				f"| Solar=OPTIMAL | Intention={intention}"
			)

			if self.agent.battery_level < 20:
				self.set_next_state(self.agent.EMERGENCY)
			elif self.agent.battery_level >= 90:
				self.set_next_state(self.agent.IDLE)
			else:
				self.set_next_state(self.agent.CHARGING)

	class SystemCheckState(FailureAwareState):
		async def run(self):
			print(
				"[HomeManagerAgent] WARNING: Communication Lost. "
				"Reverting to Safe Mode (Internal Model only)."
			)

			if self.check_battery_health():
				self.set_next_state(self.agent.EMERGENCY)
				return

			# Safe mode is conservative: rely on the internal model and keep
			# monitoring for a recovered solar update.
			self.agent.battery_level = max(0, self.agent.battery_level - 2)

			msg = await self.receive(timeout=10)
			if msg:
				self.agent.solar_status = msg.body
				print(f"  [HomeManagerAgent] << INFORM received from {msg.sender}: '{msg.body}'")

				if self.check_battery_health():
					self.set_next_state(self.agent.EMERGENCY)
					return

				if self.agent.battery_level < 20:
					self.set_next_state(self.agent.EMERGENCY)
				elif self.agent.solar_status == "OPTIMAL" and self.agent.battery_level < 90:
					self.set_next_state(self.agent.CHARGING)
				else:
					self.set_next_state(self.agent.IDLE)
				return

			intention = "Fallback monitoring with stale beliefs only"
			print(
				f"[HomeManagerAgent] State=SYSTEM_CHECK | Battery={self.agent.battery_level}% "
				f"| BatteryHealth={self.agent.battery_health} | Solar={self.agent.solar_status} "
				f"| Intention={intention}"
			)

			if self.agent.battery_level < 20:
				self.set_next_state(self.agent.EMERGENCY)
			else:
				self.set_next_state(self.agent.SYSTEM_CHECK)

	class EmergencyState(FailureAwareState):
		async def run(self):
			if self.check_battery_health():
				self.set_next_state(self.agent.EMERGENCY)
				return

			# Wait up to 5 seconds for an updated INFORM; retain last belief if none arrives.
			msg = await self.receive(timeout=5)
			if msg:
				self.agent.solar_status = msg.body
				print(f"  [HomeManagerAgent] << INFORM received from {msg.sender}: '{msg.body}'")

			solar_status = self.agent.solar_status

			# Emergency mode still consumes a small amount of energy.
			self.agent.battery_level = max(0, self.agent.battery_level - 1)

			intention = "Preserve critical battery and restore safe level"
			print(
				f"[HomeManagerAgent] State=EMERGENCY | Battery={self.agent.battery_level}% "
				f"| BatteryHealth={self.agent.battery_health} | Solar={solar_status} "
				f"| Intention={intention}"
			)

			if self.agent.battery_health == "OVERHEATED":
				self.set_next_state(self.agent.EMERGENCY)
			elif solar_status == "OPTIMAL":
				self.set_next_state(self.agent.CHARGING)
			else:
				self.set_next_state(self.agent.EMERGENCY)