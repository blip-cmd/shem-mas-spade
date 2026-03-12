"""Environment module for the SHEM Multi-Agent System."""

import random


class WeatherEnvironment:
	"""
	Simulates a deterministic day/night stress test with stochastic cloud cover.
	"""

	HIGH_SUNLIGHT_END = 10
	STRESS_END = 15
	NIGHT_END = 24

	def __init__(self, cloudy_probability=0.2, total_steps=25):
		"""
		Initialize the weather environment.

		Args:
			cloudy_probability (float): Probability of cloudy conditions (0.0 to 1.0)
			total_steps (int): Total number of sensing steps in the stress test
		"""
		self.cloudy_probability = cloudy_probability
		self.total_steps = total_steps
		self.current_timestep = -1
		self.current_wattage = 0.0
		self.current_weather = "Clear"
		self.current_phase = "BOOT"

	def _resolve_phase(self, timestep):
		if timestep <= self.HIGH_SUNLIGHT_END:
			return "HIGH_SUNLIGHT"
		if timestep <= self.STRESS_END:
			return "CLOUD_STRESS"
		return "ZERO_SUNLIGHT"

	def is_complete(self):
		"""Return True when the scripted stress test has consumed all steps."""
		return self.current_timestep >= self.total_steps - 1
        
	def update_weather(self):
		"""
		Advance the scripted stress test by one timestep.

		Returns:
			dict: Current environment snapshot for the new timestep
		"""
		if self.is_complete():
			raise StopIteration("Stress test completed")

		self.current_timestep += 1
		self.current_phase = self._resolve_phase(self.current_timestep)

		if self.current_phase == "HIGH_SUNLIGHT":
			self.current_weather = "Clear"
			self.current_wattage = random.uniform(900, 1200)
		elif self.current_phase == "CLOUD_STRESS":
			is_cloudy = random.random() < 0.8
			if is_cloudy:
				self.current_weather = "Cloudy"
				self.current_wattage = random.uniform(80, 220)
			else:
				self.current_weather = "Clear"
				self.current_wattage = random.uniform(700, 950)
		else:
			self.current_weather = "Night"
			self.current_wattage = 0.0

		return self.get_current_state()
    
	def get_current_state(self):
		"""
		Get the current state of the environment without advancing time.
		"""
		return {
			"timestep": self.current_timestep,
			"phase": self.current_phase,
			"wattage": self.current_wattage,
			"weather": self.current_weather,
			"is_cloudy": self.current_weather == "Cloudy",
		}
