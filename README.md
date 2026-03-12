# shem-mas-spade
Smart Home Energy Manager - Multi-Agent System. A BDI-style intelligent multi-agent system built with SPADE to optimize home energy self-sufficiency using stochastic environmental modeling.

## Day 4: FIPA-ACL Inter-Agent Communication

This implementation focuses on:
- **FIPA-ACL Messaging**: SolarAgent sends `INFORM` performative messages to the HomeManagerAgent
- **Message Templates**: HomeManagerAgent filters its mailbox with a SPADE `Template` to accept only `INFORM` messages
- **Belief Update**: Manager's FSM reads real messages instead of random simulation to update its internal solar status belief
- **Full Communication Loop**: Both agents are JID-aware and exchange structured XMPP messages each sensing cycle

### Project Structure

```
shem-mas-spade/
├── core/
│   └── environment.py      # Stochastic weather environment
├── agents/
│   ├── solar_agent.py      # Simple reflex agent — senses & sends INFORM messages
│   └── manager_agent.py    # Model-based FSM agent — receives messages & updates beliefs
├── main.py                 # System entry point (wires agent JIDs)
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

### Features

#### WeatherEnvironment (core/environment.py)
- Stochastic weather simulation with 20% cloudy probability
- Cloudy conditions: 50W–150W output
- Clear conditions: 800W–1200W output
- Implements realistic environmental uncertainty

#### SolarAgent (agents/solar_agent.py)
- Simple Reflex Agent architecture
- Periodic sensing every 3 seconds
- Status classification: `"LOW"` (<300W) or `"OPTIMAL"` (≥300W)
- **Day 4**: Composes a FIPA-ACL `Message` with `performative=inform` and `body=status`, then `await self.send(msg)` to the Manager's JID

#### HomeManagerAgent (agents/manager_agent.py)
- Model-Based Agent with a 3-state FSM: `IDLE → CHARGING ↔ EMERGENCY`
- Tracks `battery_level` as its internal world model
- **Day 4**: Registers the FSM with an `inform` `Template`; `IdleState` and `EmergencyState` call `await self.receive(timeout=5)` — if a message arrives its `body` updates the agent's `solar_status` belief, replacing all `random.choice` simulation

### Communication Protocol

```
SolarAgent                          HomeManagerAgent
    |                                       |
    |  sense wattage → classify status      |
    |  build Message(to=manager_jid)        |
    |  metadata: performative = "inform"    |
    |  body: "OPTIMAL" | "LOW"             |
    | ------- XMPP INFORM ---------------→ |
    |                                       |  receive(timeout=5)
    |                                       |  update solar_status belief
    |                                       |  FSM transition (IDLE/CHARGING/EMERGENCY)
```

### Setup Instructions

#### Prerequisites
1. **Python 3.8 or higher**
2. **XMPP Server** (for local testing):
   - Install Prosody: `sudo apt-get install prosody` (Linux)
   - Or use a public XMPP server

#### Installing Dependencies

```bash
pip install -r requirements.txt
```

#### Setting up Local XMPP Server (Prosody)

```bash
# Install Prosody
sudo apt-get install prosody

# Register both agent accounts
sudo prosodyctl adduser solar_sensor@localhost   # password: sensor123
sudo prosodyctl adduser home_manager@localhost   # password: manager123

# Start Prosody
sudo systemctl start prosody
```

### Running the System

```bash
python main.py
```

Expected output:
```
============================================================
SHEM - Smart Home Energy Manager
Day 4: FIPA-ACL Communication
============================================================

[System] Initializing Weather Environment...
[SolarAgent] Agent solar_sensor@localhost starting up...
[HomeManagerAgent] Agent home_manager@localhost starting up...
[HomeManagerAgent] FSM behavior registered (listening for INFORM messages)

[Sense #1] Solar Agent Perception:
  Weather: Clear
  Wattage: 1045.32W
  Status:  OPTIMAL
  [SolarAgent] >> INFORM sent to home_manager@localhost: 'OPTIMAL'
--------------------------------------------------
  [HomeManagerAgent] << INFORM received from solar_sensor@localhost: 'OPTIMAL'
[HomeManagerAgent] State=IDLE | Battery=48% | Solar=OPTIMAL | Intention=Monitor environment and preserve energy
```

Press `Ctrl+C` to stop the system gracefully.

### Architecture Notes

**Prometheus Methodology Alignment:**
- **Environment**: Stochastic model representing real-world uncertainty
- **SolarAgent Type**: Simple Reflex Agent (condition-action rules) + message sender
- **ManagerAgent Type**: Model-Based Agent (maintains belief state) + FSM controller
- **Communication**: FIPA-ACL `INFORM` performative over XMPP

**Agent Interaction Cycle:**
1. **SENSE**: SolarAgent samples the WeatherEnvironment for wattage
2. **THINK**: Classifies wattage — `IF wattage < 300 THEN "LOW" ELSE "OPTIMAL"`
3. **COMMUNICATE**: Sends a FIPA-ACL `INFORM` message to the HomeManagerAgent
4. **RECEIVE**: HomeManagerAgent's FSM state calls `receive(timeout=5)` to collect the message
5. **BELIEVE**: Manager updates its `solar_status` belief from `msg.body`
6. **TRANSITION**: FSM selects the next state (`IDLE`, `CHARGING`, or `EMERGENCY`) based on real data

### Next Steps (Day 5+)
- Add `REQUEST` / `AGREE` / `REFUSE` performatives for grid negotiation
- Introduce a GridAgent and appliance load-shedding logic
- Implement full BDI (Belief-Desire-Intention) reasoning cycle
- Persist battery state and energy logs to a time-series store
