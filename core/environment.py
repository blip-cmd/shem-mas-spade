"""Environment module for the SHEM Multi-Agent System."""

import random


class WeatherEnvironment:
	"""
	Simulates a deterministic day/night stress test with stochastic cloud cover.
	"""

	HIGH_SUNLIGHT_END = 10
	STRESS_END = 15
	NIGHT_END = 24

	def __init__(
		self,
		cloudy_probability=0.2,
		total_steps=25,
		high_sunlight_end: int = HIGH_SUNLIGHT_END,
		cloud_stress_end: int = STRESS_END,
	):
		"""
		Initialize the weather environment.

		Args:
			cloudy_probability (float): Probability of cloudy conditions (0.0 to 1.0)
			total_steps (int | None): Total number of sensing steps in the stress test.
				Set to None for open-ended simulation.
			high_sunlight_end (int): Inclusive end timestep for HIGH_SUNLIGHT phase.
			cloud_stress_end (int): Inclusive end timestep for CLOUD_STRESS phase.
		"""
		if high_sunlight_end < 0:
			raise ValueError("high_sunlight_end must be >= 0")
		if cloud_stress_end < high_sunlight_end:
			raise ValueError("cloud_stress_end must be >= high_sunlight_end")

		self.cloudy_probability = cloudy_probability
		self.total_steps = total_steps
		self.high_sunlight_end = high_sunlight_end
		self.cloud_stress_end = cloud_stress_end
		self.current_timestep = -1
		self.current_wattage = 0.0
		self.current_weather = "Clear"
		self.current_phase = "BOOT"

	def _resolve_phase(self, timestep):
		"""Map a timestep to the configured evaluation phase."""
		if timestep <= self.high_sunlight_end:
			return "HIGH_SUNLIGHT"
		if timestep <= self.cloud_stress_end:
			return "CLOUD_STRESS"
		return "ZERO_SUNLIGHT"

	def is_complete(self):
		"""Return True when the scripted stress test has consumed all steps."""
		if self.total_steps is None:
			return False
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
			is_cloudy = random.random() < self.cloudy_probability
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
