"""
Environment Module for SHEM Multi-Agent System

This module simulates a stochastic weather environment that affects
solar panel power generation. It follows the Prometheus methodology
for environment modeling in Multi-Agent Systems.
"""

import random


class WeatherEnvironment:
	"""
	Simulates a stochastic weather environment for solar energy generation.
    
	The environment uses a probabilistic model where weather conditions
	fluctuate randomly, affecting the wattage output of solar panels.
	This represents the unpredictable nature of real-world weather patterns.
    
	Attributes:
		cloudy_probability (float): Probability of cloudy weather (default: 0.2)
		current_wattage (float): Current power output in watts
		current_weather (str): Current weather condition ("Clear" or "Cloudy")
	"""
    
	def __init__(self, cloudy_probability=0.2):
		"""
		Initialize the weather environment.
        
		Args:
			cloudy_probability (float): Probability of cloudy conditions (0.0 to 1.0)
		"""
		self.cloudy_probability = cloudy_probability
		self.current_wattage = 0.0
		self.current_weather = "Clear"
        
	def update_weather(self):
		"""
		Update the weather conditions using a stochastic model.
        
		This method implements the core stochastic behavior of the environment:
		- 20% probability of cloudy weather → Low wattage (50W-150W)
		- 80% probability of clear weather → High wattage (800W-1200W)
        
		The stochastic nature models real-world uncertainty and provides
		variable percepts for the agent to sense and react to.
        
		Returns:
			tuple: (wattage: float, is_cloudy: bool)
				- wattage: Current power output in watts
				- is_cloudy: Boolean indicating if conditions are cloudy
		"""
		# Stochastic event: Determine weather condition using probability
		is_cloudy = random.random() < self.cloudy_probability
        
		if is_cloudy:
			# Cloudy conditions: Low solar power generation
			self.current_wattage = random.uniform(50, 150)
			self.current_weather = "Cloudy"
		else:
			# Clear conditions: Optimal solar power generation
			self.current_wattage = random.uniform(800, 1200)
			self.current_weather = "Clear"
        
		return (self.current_wattage, is_cloudy)
    
	def get_current_state(self):
		"""
		Get the current state of the environment without updating.
        
		Returns:
			dict: Current environment state with wattage and weather condition
		"""
		return {
			"wattage": self.current_wattage,
			"weather": self.current_weather,
			"is_cloudy": self.current_weather == "Cloudy"
		}
