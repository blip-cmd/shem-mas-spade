# Design and Implementation of a BDI-Style Smart Home Energy Manager (SHEM)

**Author:** Ryan Nii Akwei Brown (ryanniiakweibrown1@gmail.com)  
**Methodology:** Prometheus Agent-Oriented Software Engineering  
**Platform:** Smart Python Agent Development Environment (SPADE)  
**Repository:** [blip-cmd/shem-mas-spade](https://github.com/blip-cmd/shem-mas-spade)

---

## Contents

- [1. Introduction](#1-introduction)
- [2. Problem Context and Statistics](#2-problem-context-and-statistics)
- [3. Agent Design and Behaviours](#3-agent-design-and-behaviours)
- [4. System Classification](#4-system-classification)
  - [4.1 Environment](#41-environment)
  - [4.2 Agent Types & PEAS](#42-agent-types--peas)
- [5. Prometheus Methodology Application](#5-prometheus-methodology-application)
  - [5.1 System Specification](#51-system-specification)
  - [5.2 Architectural Design](#52-architectural-design)
  - [5.3 Interaction Design](#53-interaction-design)
  - [5.4 Detailed Design](#54-detailed-design)
- [6. Implementation and Execution](#6-implementation-and-execution)
  - [6.1 Technology Stack and Setup](#61-technology-stack-and-setup)
  - [6.2 Agent Logic Mapping](#62-agent-logic-mapping)
  - [6.3 Dynamic System Design & FSM](#63-dynamic-system-design--fsm)
  - [6.4 Challenges and Limitations](#64-challenges-and-limitations)
- [7. Technical Value](#7-technical-value)
- [8. Conclusion](#8-conclusion)

---

## 1. Introduction

Welcome to the technical documentation for SHEM (Smart Home Energy Manager). This project bridges the gap between theoretical agent-oriented software engineering and a practical implementation. Using the Prometheus methodology, I designed a Multi-Agent System (MAS) that autonomously manages a home's solar power and battery reserves.

Rather than relying on brittle, hard-coded scripts, SHEM utilises intelligent agents that perceive their environment, maintain internal beliefs, and make proactive decisions to achieve energy self-sufficiency.

## 2. Problem Context and Statistics

Integrating solar power into residential homes introduces significant uncertainty due to dynamic weather variability and grid instability (such as random blackouts). Centralised, static control systems fail in these environments because they cannot adapt to sudden changes or partial sensor failures.

An agent-based solution is required because this problem space is highly distributed and requires autonomous decision-making. The system must dynamically balance two competing goals: maximising the use of free solar energy while safely preserving battery health.

Think of SHEM as a software-only system, deployed in a home with open sky, with the sky, the sun, and the physical solar panels on the roof of the building, like your neighbourhood. How do current solar panel systems work and how is SHEM gonna be relevant.

## 3. Agent Design and Behaviours

To effectively manage this environment, SHEM employs two distinct agent architectures:

- **SolarAgent – A Simple Reflex Agent:**  
  This agent operates purely on a sense-act cycle. It reads the current wattage from the environment and instantly categorises the weather state (e.g., `OPTIMAL` or `LOW`). It has no history.

- **HomeManagerAgent – A Model-Based / Goal-Driven Agent:**  
  This is my BDI-style (Belief-Desire-Intention) "Brain". It maintains an internal Belief about the battery's State of Charge (SoC). It pursues long-term Goals by transitioning through Plans based on environmental events.

## 4. System Classification

Before diving into Prometheus, I formally define the operational boundaries using the PEAS framework.

### 4.1 Environment

The simulated home environment is mathematically challenging:
- **Dynamic & Stochastic:** Sunlight intensity changes unpredictably based on a probabilistic cloud cover model (e.g., 20% to 80% cloud probability depending on the phase).
- **Partially Observable:** The agent cannot see the entire grid, only local sensor readings.

### 4.2 PEAS

- **Performance Measure:** Percentage of energy cost saved and 100% uptime for critical appliances.
- **Environment:** Simulated home grid with fluctuating weather.
- **Actuators:** Virtual load-shedding switches and battery charge controllers.
- **Sensors:** Virtual Solar Pyranometer and Battery Voltage Meter.

## 5. Prometheus Methodology Application

The core of this project is the rigorous application of Prometheus Methodology, progressing systematically from abstract goals to deployable code.

### 5.1 System Specification 

The first phase answers what the system should do, ignoring how it does it. I extracted Goals, defined Scenarios, and mapped Functionalities. I decomposed my top-level goal (Energy Self-Sufficiency) into actionable sub-goals, using the Prometheus standard of representing goals as ovals.
 
![System Goal Hierarchy Diagram](<Figure 1 - System Goal Hierarchy Diagram.png>)  
*Figure 1: System Goal Hierarchy Diagram*

**System Scenarios (Use Cases):**
1. **Optimal Charging:** The sun is shining brightly. The reflex agent perceives high wattage, and the manager agent, noting the battery is at 60%, decides to route power to the battery until it hits 100%.
2. **Stochastic Cloud Cover:** Heavy clouds suddenly block the sun. The manager evaluates its 80% battery belief and dynamically drops its charging goal, transitioning to `IDLE` to keep standard loads running safely.
3. **Critical Battery Depletion:** The grid fails at night. As power drains to 19%, the agent proactively triggers an `EMERGENCY` state, shedding non-essential loads to preserve the battery lifespan.
4. **Sensor Failure (Robustness):** The solar sensor disconnects. Instead of crashing, the manager times out, realises the sensor is missing, and falls back to its internal decay model in a `SYSTEM_CHECK` state.

### 5.2 Architectural Design

I group functionalities into Agents and determine how they couple. The System Overview Diagram is the single most important artefact in Prometheus. In accordance with the book's formal shapes, agents are boxes, data stores are cylinders, and percepts/actions bridge the system.

![System Overview Diagram](<Figure 2 - System Overview Diagram.png>)  
*Figure 2: System Overview Diagram*

### 5.3 Interaction Design 

I utilise Agent UML (AUML) to formalise interaction protocols, ensuring all valid message sequences, including alternatives and failure states, are comprehensively modelled. Communication follows the asynchronous FIPA-ACL standard. 
 
![AUML Weather-Monitoring Protocol](<Figure 3 - AUML Weather-Monitoring Protocol.png>)  
*Figure 3: AUML Weather-Monitoring Protocol*

### 5.4 Detailed Design

Zooming into the HomeManagerAgent, I define its internal Capabilities using an Agent Overview Diagram, which describes the message flow between internal modules and data. The Manager is decomposed into:
- **EnergyMonitoringCapability:** Parses incoming FIPA-ACL messages and monitors timeouts.
- **BatteryManagementCapability:** Executes plans based on updated beliefs using an internal Finite State Machine.
 
![Agent Overview Diagram](<Figure 4 - Agent Overview Diagram (HomeManagerAgent).png>)  
*Figure 4: Agent Overview Diagram (HomeManagerAgent)*

## 6. Implementation and Execution

These theoretical BDI and agent-oriented designs are mapped to executable code using the Smart Python Agent Development Environment (SPADE) framework.

### 6.1 Technology Stack and Setup

The implementation utilises Python 3.9+ and SPADE 4.0.3. XMPP message routing is handled locally using a Prosody server. SPADE was chosen because its native behaviour classes (`CyclicBehaviour`, `FSMBehaviour`) perfectly map to Prometheus capability decomposition, and it inherently supports FIPA-ACL messaging.

### 6.2 Agent Logic Mapping

1. **SolarAgent:** Directly maps to a `spade.behaviour.PeriodicBehaviour` running every 3 seconds. It enacts a simple Condition-Action rule: if wattage < 300W, status is `LOW`; otherwise `OPTIMAL`. It sends this using the FIPA-ACL `INFORM` performative.
2. **HomeManagerAgent:** Uses two concurrent SPADE behaviours:
   - **EnergyMonitoringCapability:** A `CyclicBehaviour` that uses a `SPADE Template()` to actively filter for `INFORM` messages. Crucially, it features a 10-second timeout to handle sensor failure autonomously.
   - **BatteryManagementCapability:** An `FSMBehaviour` mapping proactive and reactive goal plans to four distinct states: `IDLE`, `CHARGING`, `SYSTEM_CHECK`, and `EMERGENCY`.

### 6.3 Dynamic System Design & FSM

To handle the dynamic environment and enforce rationality, the HomeManagerAgent uses a Finite State Machine (FSM). Every state inherits from a `FailureAwareState` base class, which simulates a 5% probabilistic battery overheat. If an overheat occurs, the agent dynamically drops its Achievement Goal and triggers an `EMERGENCY`.
 
![FSM State Transition Diagram](<Figure 5 - FSM State Transition Diagram.png>)  
*Figure 5: FSM State Transition Diagram*

### 6.4 Challenges and Limitations

The primary implementation challenge was handling asynchronous startup race conditions via XMPP. If the SolarAgent fired before the Manager's message templates were fully bound to Prosody, the initial percepts were lost. This was resolved by implementing an `asyncio.sleep()` delay during bootstrapping. A current limitation is that `spade.df` (Directory Facilitator) is deprecated in SPADE version 4.0.3; therefore, DF service discovery was mapped conceptually rather than enforced programmatically, relying on direct FIPA-ACL routing instead.

## 7. Technical Value

This project stands as a rigorous demonstration of advanced Agent-Oriented Software Engineering. It elevates code from mere scripts to a methodologically sound Multi-Agent System.

- **Autonomy & Reactivity:** Proven by the agent's stochastic FSM transitions and autonomous operation via SPADE.
- **Social Ability:** Proven via asynchronous FIPA-ACL communication across an XMPP server.
- **Rationality & Robustness:** Proven by the agent safely dropping its Achievement Goal (Charging) to enforce its Maintenance Goal (Battery Health) during a cloud drop, a 5% stochastic overheat, or a 10-second communication timeout.

## 8. Conclusion

The Smart Home Energy Manager (SHEM) successfully proves that Prometheus Agent-Oriented Software Engineering is highly applicable to IoT and Smart Grid problems. By mapping clear system goals down to specific capabilities and AUML protocols, and finally implementing them robustly in SPADE Python, I have built a resilient, decentralised intelligence capable of optimising power independently in an unpredictable world.
