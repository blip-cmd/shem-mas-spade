# shem-mas-spade
Smart Home Energy Manager - Multi-Agent System. A BDI-style intelligent multi-agent system built with SPADE to optimize home energy self-sufficiency using stochastic environmental modeling.

## Day 2: Perception and Environment Modeling

This implementation focuses on:
- **Stochastic Environment Simulation**: WeatherEnvironment with probabilistic weather conditions
- **Simple Reflex Agent**: SolarAgent that senses and reacts to environmental conditions
- **Sense-Think-Act Cycle**: Periodic behavior monitoring solar energy generation

### Project Structure

```
shem-mas-spade/
├── core/
│   └── environment.py      # Stochastic weather environment
├── agents/
│   └── solar_agent.py      # Simple reflex agent for solar monitoring
├── main.py                 # System entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Features

#### WeatherEnvironment (core/environment.py)
- Stochastic weather simulation with 20% cloudy probability
- Cloudy conditions: 50W-150W output
- Clear conditions: 800W-1200W output
- Implements realistic environmental uncertainty

#### SolarAgent (agents/solar_agent.py)
- Simple Reflex Agent architecture
- Periodic sensing every 3 seconds
- Status classification: "LOW" (<300W) or "OPTIMAL" (≥300W)
- Implements the Sense-Think-Act cycle

### Setup Instructions

#### Prerequisites
1. **Python 3.8 or higher**
2. **XMPP Server** (for local testing):
	 - Install Prosody: `sudo apt-get install prosody` (Linux)
	 - Or use a public XMPP server

#### Installing Dependencies

```bash
# Install SPADE and dependencies
pip install -r requirements.txt
```

#### Setting up Local XMPP Server (Prosody)

```bash
# Install Prosody
sudo apt-get install prosody

# Create a user for the agent
sudo prosodyctl adduser solar_sensor@localhost
# Password: sensor123

# Start Prosody
sudo systemctl start prosody
```

### Running the System

```bash
# Run the SHEM system
python main.py
```

Expected output:
```
============================================================
SHEM - Smart Home Energy Manager
Day 2: Perception and Environment Modeling
============================================================

[System] Initializing Weather Environment...
[System] Weather Environment initialized
[SolarAgent] Agent solar_sensor@localhost starting up...
[SolarAgent] Sensing behavior registered with 3-second period

[Sense #1] Solar Agent Perception:
	Weather: Clear
	Wattage: 1045.32W
	Status:  OPTIMAL
--------------------------------------------------
```

Press `Ctrl+C` to stop the system gracefully.

### Architecture Notes

**Prometheus Methodology Alignment:**
- **Environment**: Stochastic model representing real-world uncertainty
- **Agent Type**: Simple Reflex Agent (condition-action rules)
- **Perception**: Direct sensing of environmental state
- **Action**: Logging and status classification

**Sense-Think-Act Cycle:**
1. **SENSE**: Agent perceives wattage and weather from environment
2. **THINK**: Applies rule: IF wattage < 300 THEN "LOW" ELSE "OPTIMAL"
3. **ACT**: Logs the status for monitoring

### Next Steps (Day 3+)
- Add battery management agent
- Implement inter-agent communication
- Add BDI (Belief-Desire-Intention) architecture
- Integrate grid interaction logic
