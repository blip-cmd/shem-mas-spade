"""
Home Manager Agent Module for SHEM Multi-Agent System

This module implements a Model-Based Agent using a Finite State Machine (FSM)
to maintain internal state (battery level) and react to changing conditions.
"""

import asyncio

from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.template import Template


class HomeManagerAgent(Agent):
	"""
	A Model-Based Agent that manages home battery behavior.

	The agent tracks battery level as its internal model and transitions
	between IDLE, CHARGING, and EMERGENCY states according to maintenance
	and charging goals.
	"""

	IDLE = "IDLE"
	CHARGING = "CHARGING"
	EMERGENCY = "EMERGENCY"

	def __init__(self, jid, password, solar_jid, verify_security=False):
		super().__init__(jid, password, verify_security=verify_security)
		self.solar_jid = solar_jid
		self.battery_level = 50
		# Belief: last known solar status received from SolarAgent
		self.solar_status = "LOW"

	async def setup(self):
		print(f"[HomeManagerAgent] Agent {self.jid} starting up...")

		fsm = self.BatteryFSM()
		fsm.add_state(name=self.IDLE, state=self.IdleState(), initial=True)
		fsm.add_state(name=self.CHARGING, state=self.ChargingState())
		fsm.add_state(name=self.EMERGENCY, state=self.EmergencyState())

		# Register all legal transitions among operational states.
		fsm.add_transition(source=self.IDLE, dest=self.IDLE)
		fsm.add_transition(source=self.IDLE, dest=self.CHARGING)
		fsm.add_transition(source=self.IDLE, dest=self.EMERGENCY)
		fsm.add_transition(source=self.CHARGING, dest=self.CHARGING)
		fsm.add_transition(source=self.CHARGING, dest=self.IDLE)
		fsm.add_transition(source=self.CHARGING, dest=self.EMERGENCY)
		fsm.add_transition(source=self.EMERGENCY, dest=self.EMERGENCY)
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

	class IdleState(State):
		async def run(self):
			# Wait up to 5 seconds for a real FIPA-ACL INFORM from the SolarAgent.
			msg = await self.receive(timeout=5)
			if msg:
				self.agent.solar_status = msg.body
				print(f"  [HomeManagerAgent] << INFORM received from {msg.sender}: '{msg.body}'")

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

	class ChargingState(State):
		async def run(self):
			await asyncio.sleep(3)

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

	class EmergencyState(State):
		async def run(self):
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
				f"| Solar={solar_status} | Intention={intention}"
			)

			if solar_status == "OPTIMAL":
				self.set_next_state(self.agent.CHARGING)
			else:
				self.set_next_state(self.agent.EMERGENCY)