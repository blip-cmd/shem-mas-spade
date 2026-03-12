# SHEM MAS

Smart Home Energy Manager for DCIT 403. This repository implements a small multi-agent system in SPADE where a solar sensing agent and a home manager agent coordinate around renewable energy availability, battery charging, and stress-test evaluation.

## Project Summary

The project models a smart home as a distributed intelligent system:

- The SolarAgent senses weather-dependent generation and sends symbolic updates.
- The HomeManagerAgent maintains internal battery beliefs and reacts through an FSM.
- The WeatherEnvironment provides both normal solar conditions and a Day 6 stress scenario.
- The evaluation pipeline writes runtime metrics to evaluation_results.csv and prints a final summary at shutdown.

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

This project aligns its implementation with the course labs as follows.

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
- Implements the Day 6 evaluation profile:
  - T=0-10: high sunlight
  - T=11-15: cloud stress with 80% cloud probability
  - T=16-24: zero sunlight

### Evaluation Pipeline

- Writes structured runtime results to evaluation_results.csv.
- Tracks three summary metrics:
  - Total Grid Energy Saved
  - Battery Safety Violations
  - Average Reaction Time

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
sudo systemctl start prosody
```

Use these passwords when prompted:

- solar_sensor@localhost: sensor123
- home_manager@localhost: manager123

### 4. Run the main MAS simulation

```bash
python main.py
```

### 5. Run the Day 6 stress test directly

```bash
python stress_test.py
```

At the end of the run, the system prints:

- Total Grid Energy Saved: X units
- Battery Safety Violations: X times
- Average Reaction Time: X ms

It also writes detailed step-by-step data to evaluation_results.csv.

### 6. Generate the optional battery plot

After a stress test has produced evaluation_results.csv, run:

```bash
python plots.py
```

This generates battery_level_over_time.png in the project root.

## Key Findings

The repository currently does not include a committed Day 6 evaluation_results.csv file, so the points below are grounded in the implemented evaluation pipeline and a deterministic smoke validation of that pipeline.

- The Day/Night stress profile correctly separates high-generation, cloud-stress, and zero-solar phases across 25 timesteps.
- The evaluation logger produces full CSV coverage for both sensing events and manager state transitions, which makes the final metrics auditable after each run.
- In smoke validation of the logging flow, the evaluation path recorded a safety-threshold breach when battery level dropped below the configured limit, confirming that Battery Safety Violations are counted at the root condition rather than inferred later.
- Reaction time measurement is captured at message handoff time using per-message timestamps, so communication responsiveness can be compared across future runs.

For the final report submission, rerun stress_test.py against a working local XMPP server and replace this section with the exact values printed at shutdown.

## Expected Outputs

Successful Day 6 execution should produce:

- evaluation_results.csv
- Console summary of grid savings, safety violations, and reaction time
- Optional battery_level_over_time.png when plots.py is used

## Notes

- JIDs and passwords are currently hardcoded for local coursework testing.
- The project assumes localhost XMPP connectivity unless the credentials in main.py are changed.
- The plotting script is intentionally lightweight and only depends on the CSV output from Day 6.
