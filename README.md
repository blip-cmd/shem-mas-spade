# SHEM MAS

Smart Home Energy Manager (SHEM) for DCIT 403. This repository presents a SPADE-based multi-agent system in which a solar sensing agent and a home energy manager coordinate battery usage under both nominal and stress conditions.

## Project Summary

The project models a smart home as a distributed intelligent system with explicit perception, communication, and control layers:

- SolarAgent performs periodic sensing and publishes symbolic solar-state updates.
- HomeManagerAgent maintains internal beliefs and applies finite-state control for battery management.
- WeatherEnvironment provides both stochastic baseline behavior and a bounded Day 6 stress profile.
- The evaluation pipeline records runtime metrics to evaluation_results.csv and reports final summary statistics.

## Project Structure

```text
shem-mas-spade/
├── agents/
│   ├── __init__.py
│   ├── manager_agent.py
│   └── solar_agent.py
├── core/
│   ├── __init__.py
│   ├── environment.py
│   └── logger.py
├── main.py
├── plots.py
├── requirements.txt
├── stress_test.py
└── README.md
```

## Theory Applied

This implementation maps directly to the DCIT 403 laboratory sequence.

| Course Lab | Theory Applied in This Repo | Concrete Implementation |
| --- | --- | --- |
| Lab 2: Perception and Environment Modeling | Agents reason over an external environment instead of fixed inputs. | WeatherEnvironment models solar conditions and exposes percepts as wattage, weather, and phase. |
| Lab 3: Reactive Agent Behavior | Condition-action rules drive immediate response to percepts. | SolarAgent classifies each reading as LOW or OPTIMAL and acts without long-horizon planning. |
| Lab 3: Reactive Control with FSM | Reactive behavior can also be structured as explicit states. | HomeManagerAgent uses an FSM with IDLE, CHARGING, SYSTEM_CHECK, and EMERGENCY states. |
| Lab 4: Agent Communication | Agents exchange structured symbolic messages rather than shared variables. | SolarAgent sends FIPA-ACL INFORM messages and HomeManagerAgent filters them with a SPADE Template. |
| Lab 12: System Evaluation | Multi-agent systems should be evaluated under stress with measurable metrics. | Day/Night stress logic, CSV logging, grid-energy estimate, safety violation counting, and reaction-time measurement. |
| Lab 13: Packaging and Documentation | A finished MAS should be runnable, documented, and ready for demonstration. | Final README, dependency list, stress-test entry point, and optional plotting script. |

## Core Features

### SolarAgent

- Implements a simple reflex agent.
- Senses the environment every cycle and converts wattage into LOW or OPTIMAL.
- Sends FIPA-ACL INFORM messages to the manager with extra evaluation metadata.

### HomeManagerAgent

- Implements a model-based controller with a finite-state machine.
- Tracks battery level, solar status, and battery health as internal beliefs.
- Logs every state transition together with current battery level and reaction time.

### WeatherEnvironment

- Supports normal probabilistic weather behavior through its cloudy probability parameter.
- Implements the evaluation profile:
  - T=0-10: high sunlight
  - T=11-15: cloud stress with 80% cloud probability
  - T=16-24: zero sunlight

### Evaluation Pipeline

- Writes structured runtime results to evaluation_results.csv.
- Tracks three summary metrics:
  - Total Grid Energy Saved
  - Battery Safety Violations
  - Average Reaction Time

## How Metrics Are Calculated

The end-of-run summary is built from the logger in `core/logger.py` and timing metadata exchanged between agents.

### 1) Total Grid Energy Saved

This metric accumulates two contributors over time:

- **Solar contribution (per sensing cycle):**
  - `solar_saved = min(wattage / 100, 8.0)`
  - `min(...)` applies a cap so one very high-wattage moment does not dominate the total score.
  - The `8.0` value is an evaluation/scoring normalization cap, not a physical limit on solar generation.
  - Logged by `log_solar_cycle(...)`.
- **Battery support contribution (per manager state transition):**
  - `battery_support = max(0, previous_battery_level - current_battery_level)`
  - `max(0, ...)` prevents negative contribution when battery level increases.
  - Logged by `log_state_transition(...)`.

Final value:

- `Total Grid Energy Saved = sum(solar_saved) + sum(battery_support)`

### 2) Battery Safety Violations

At each manager transition, an **unsafe condition** is defined as:

- `battery_level < safe_battery_threshold` (default threshold: 20), **or**
- `battery_health != "HEALTHY"`

The violation counter increases only when the system **enters** an unsafe period (safe → unsafe edge), not on every unsafe timestep. This avoids overcounting a continuous unsafe streak.

### 3) Average Reaction Time

When the SolarAgent sends an INFORM, it includes `sent_at = time.perf_counter()` in message metadata. On receipt, HomeManagerAgent computes:

- `reaction_time_ms = (time.perf_counter() - sent_at) * 1000`

Only transitions with a measured value are included. The final summary reports:

- `Average Reaction Time = arithmetic mean of collected reaction_time_ms values`
- If no timing samples exist, the project reports `0.0 ms`.

## How To Run

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up an XMPP server

SPADE requires an XMPP server. A local Prosody setup is the simplest option.

```bash
sudo apt-get install prosody
sudo prosodyctl adduser solar_sensor@localhost
sudo prosodyctl adduser home_manager@localhost
sudo service prosody start
sudo service prosody status
```
```bash
# Clean up saved users in Prosody (optional)
sudo prosodyctl deluser solar_sensor@localhost
sudo prosodyctl deluser home_manager@localhost
```

If you are running inside a non-privileged dev container, `service prosody start` may fail with permission errors (for example: cannot create `/run/prosody` or cannot set gid). In that case, run Prosody outside the container (host OS or VM), then point the agent JIDs in `main.py` to that reachable XMPP domain/host.

Use these passwords when prompted:

- solar_sensor@localhost: sensor123
- home_manager@localhost: manager123

If your XMPP server is not `localhost`, set environment variables before running the app:

```bash
export XMPP_DOMAIN=your-xmpp-hostname
export SOLAR_AGENT_JID=solar_sensor@your-xmpp-hostname
export MANAGER_AGENT_JID=home_manager@your-xmpp-hostname
export SOLAR_AGENT_PASSWORD=sensor123
export MANAGER_AGENT_PASSWORD=manager123
```

### 4. Run the main MAS simulation (open-ended)

```bash
python main.py
```

### 5. Run the stress test for a bounded evaluation

The stress test runs a scripted multi-phase scenario to systematically evaluate system behavior under varying weather and battery conditions. Each phase presents different environmental conditions:

- **HIGH_SUNLIGHT**: Clear skies with maximum solar generation (900–1200 W).
- **CLOUD_STRESS**: Variable cloud cover (configurable probability) with reduced wattage (80–950 W).
- **ZERO_SUNLIGHT**: Night phase with no solar generation (0 W).

Basic run:

```bash
python stress_test.py
```

Optional configuration:

```bash
python stress_test.py --steps 60 --high-sunlight-duration 15 --cloud-stress-duration 20 --cloudy-probability 0.95
```

**Configurable stress-test parameters:**

- `--steps`: total number of stress-test steps (default `25`)
- `--high-sunlight-duration`: number of HIGH_SUNLIGHT timesteps at start (default `10`)
- `--cloud-stress-duration`: number of CLOUD_STRESS steps after high sunlight (default `5`)
- `--cloudy-probability`: cloud probability in the environment (default `0.8`)

**Suggested stress-test presets:**

```bash
# Baseline (reference): evaluation day original profile
python stress_test.py --steps 25 --high-sunlight-duration 10 --cloud-stress-duration 5 --cloudy-probability 0.8

# Extended cloud pressure with longer sunlight
# Tests system resilience under sustained cloud stress and longer charging windows.
python stress_test.py --steps 60 --high-sunlight-duration 15 --cloud-stress-duration 20 --cloudy-probability 0.95

# Maximum cloud stress during extended stress window
# Tests battery management under severe cloud conditions (100% cloud probability).
python stress_test.py --steps 50 --high-sunlight-duration 8 --cloud-stress-duration 25 --cloudy-probability 1.0

# Best-case control comparison (clear skies)
# Validates charging and idle behavior without cloud interference.
python stress_test.py --steps 30 --high-sunlight-duration 12 --cloud-stress-duration 5 --cloudy-probability 0.0
```

**Output and results:**

- Total Grid Energy Saved: X units
- Battery Safety Violations: X times
- Average Reaction Time: X ms

It also writes per-step evaluation records to evaluation_results.csv.

### 6. Generate the optional battery plot

After a stress test has produced evaluation_results.csv, run:

```bash
python plots.py
```

This generates battery_level_over_time.png in the project root.

## Key Findings

The following findings are derived from the an evaluation_results.csv run earlier on:

- Total Grid Energy Saved: **103.88 units**
- Battery Safety Violations: **0 times**
- Average Reaction Time: **0.73 ms**

Interpretation of these results:

- The Day/Night profile maintained safe battery operation throughout this recorded run.
- The manager responded to incoming solar updates with sub-millisecond average latency, indicating low communication overhead in the local setup.
- Grid-energy savings remained positive across high-sun, cloud-stress, and zero-sunlight periods, showing that the hybrid solar-plus-battery policy maintained useful autonomy.

## Expected Outputs

Successful execution would produce:

- an updated evaluation_results.csv
- Console summary of grid savings, safety violations, and reaction time
- Optional battery_level_over_time.png when plots.py is used

## Notes

- JIDs and passwords are currently hardcoded for local coursework testing.
- The project assumes localhost XMPP connectivity unless credentials in main.py are changed.
- The plotting script is intentionally lightweight and only depends on the evaluation_results.csv
