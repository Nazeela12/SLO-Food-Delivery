FoodPulse — SLO Decision & Reliability Console
Project Overview
FoodPulse is a locality-aware reliability decision-support prototype for a food-delivery platform whose operational demand and service reliability can change with local weather conditions.

The system connects service-level indicators (SLIs), service-level objectives (SLOs), error-budget status, customer impact, weather severity, support incidents, reliability tasks, feature plans, human approval/override decisions, SQLite audit records, telemetry recovery, and sensitivity analysis.

Problem Statement
The system helps a reliability team:

Measure service reliability using SLI/SLO data.

Detect error-budget risk.

Quantify user impact.

Include weather severity as an operational signal.

Connect measured evidence to reliability work.

Handle duplicate, delayed, and out-of-order telemetry safely.

Require human approval before recording a final decision.

Preserve an auditable decision history.

Test whether reliability priorities remain stable when decision weights change.

Architecture
                    FOODPULSE
                       |
                       v
              +-------------------+
              | Operational Data  |
              +-------------------+
              | Service telemetry |
              | Support incidents |
              | Weather data      |
              | Reliability work  |
              | Feature plans     |
              +---------+---------+
                        |
                        v
              +-------------------+
              | Decision Engine   |
              +-------------------+
              | SLI / SLO         |
              | Error Budget      |
              | User Impact       |
              | Weather Factor    |
              +---------+---------+
                        |
                        v
              +-------------------+
              | Priority Score    |
              | P1 / P2 / P3 / P4|
              +---------+---------+
                        |
             +----------+----------+
             |                     |
             v                     v
      Human Decision        SQLite Audit Store
      Approve / Reject      Decision history
      / Override            + timestamps

Telemetry Events
       |
       v
Pydantic Validation
       |
       v
Event Processor
       |
       +--> Duplicate detection
       +--> Delayed-event detection
       +--> Out-of-order detection
       |
       v
Protected Order State
Decision Model
Baseline weights:

Evidence	Weight
SLO risk	40%
User impact	35%
Error-budget risk	15%
Weather	10%
Priority classification:

Score	Priority
>= 60	P1 - Critical
>= 40	P2 - High
>= 20	P3 - Medium
< 20	P4 - Low
The model provides decision support. A human operator must approve, reject, or override the recommendation.

SLI, SLO and Error Budget
The service SLI is:

SLI = (on-time orders / total orders) × 100
The current SLO target is 95%.

The system evaluates SLO risk and remaining error budget from the measured service failure rate.

User Impact
User impact combines measurable operational signals including customer complaints, failed orders, and total orders. The resulting score contributes to reliability prioritization.

Weather Factor
Current rainfall thresholds:

< 5 mm       -> 0.0
5–14.99 mm   -> 0.4
15–29.99 mm  -> 0.7
>= 30 mm     -> 1.0
Weather contributes 10% to the baseline priority score.

Telemetry Event Recovery
The event processor protects order state from problematic event delivery patterns.

Duplicate events: an already-processed event_id is ignored.

Out-of-order events: an older event cannot overwrite newer order state.

Delayed events: events beyond the configured delay threshold are detected.

Schema validation: telemetry is validated with Pydantic before processing.

Required telemetry fields:

event_id
order_id
event_time
status
Unexpected extra fields are rejected.

Human-in-the-Loop Governance
Operators can choose:

Approved
Rejected
Overridden
An override requires a reason.

Saved decisions include the decision ID, timestamp, locality, recommended priority/action, human decision, override reason, priority score, SLI, SLO, user impact, and rainfall.

SQLite Audit Persistence
The project now uses SQLite instead of relying on CSV as the primary audit state.

Database:

data/decision_audit.db
The audit store creates a decision_audit table and uses transactional writes. SQLite WAL mode is enabled to improve concurrent read/write behavior.

Legacy CSV migration logic is retained in the dashboard for existing audit data.

Sensitivity Analysis
Five weighting scenarios are tested:

Baseline

Higher SLO Risk

Higher User Impact

Higher Error Budget

Higher Weather

Each scenario keeps total weight at 100%.

The dashboard reports the number of scenarios, baseline priority, priority stability, score range, and weighting scenario comparison.

Priority stability is the percentage of tested scenarios whose priority classification matches the baseline. This is an experiment and does not prove that one weighting scheme is universally correct.

Dashboard
The Streamlit dashboard contains:

Overview
SLI, SLO, error budget, user impact, priority score, rainfall, recommendation, decision inputs, and decision logic.

Evidence & Work
Service telemetry, support evidence, weather evidence, reliability tasks, and feature plans.

Governance & Audit
Human decision selection, override reason, SQLite persistence, and audit history.

Validation
Reliability-priority justification experiment, evidence details, baseline weights, sensitivity analysis, and priority stability.

Reliability Tests
Demonstration of duplicate, delayed, and out-of-order telemetry handling and protected final order state.

Project Structure
SLO-Food_Delivery/
├── dashboard/
│   └── app.py
├── data/
│   ├── service_metrics.csv
│   ├── support_incidents.csv
│   ├── weather.csv
│   ├── reliability_tasks.csv
│   ├── feature_plans.csv
│   ├── orders.csv
│   └── decision_audit.db
├── src/
│   ├── __init__.py
│   ├── decision_engine.py
│   ├── event_processor.py
│   ├── priority_metrics.py
│   ├── audit_store.py
│   ├── telemetry_schema.py
│   └── sensitivity_analysis.py
├── tests/
│   ├── test_decision_engine.py
│   ├── test_event_processor.py
│   ├── test_priority_metrics.py
│   ├── test_audit_store.py
│   └── test_sensitivity_analysis.py
├── .gitignore
├── requirements.txt
└── README.md
Installation
Clone
git clone https://github.com/Nazeela12/SLO-Food-Delivery.git
cd SLO-Food-Delivery
Create virtual environment
Windows:

py -m venv .venv
Activate
.venv\Scripts\Activate.ps1
If PowerShell activation is blocked, use:

.venv\Scripts\python.exe
Install dependencies
py -m pip install -r requirements.txt
Run the Dashboard
streamlit run dashboard/app.py
Run Tests
python -m pytest
Current local development checkpoint:

16 passed
Validation Experiment
A reliability priority is considered evidence-justified when at least one measurable condition indicates operational need:

SLO breach

High user impact

Low remaining error budget

The dashboard reports the measured justification percentage and detailed evidence.

Limitations
The datasets are prototype/validation datasets rather than production telemetry.

Weather input is represented through rainfall values in the supplied dataset.

Decision weights are manually defined and evaluated through predefined sensitivity scenarios.

Sensitivity analysis does not cover every possible combination of weights.

The dashboard is a decision-support interface and does not automatically execute production changes.

Human approval remains necessary for final decisions.

Current Development Status
Implemented:

SLO/SLI decision engine

Error-budget calculation

User-impact calculation

Weather-aware scoring

P1–P4 classification

Evidence-based reliability prioritization

Human-in-the-loop governance

SQLite audit persistence

Pydantic telemetry validation

Duplicate/delayed/out-of-order event recovery

Sensitivity analysis

Streamlit decision dashboard

Automated test suite

Remaining engineering work:

FastAPI API layer

API integration and testing

CI test workflow

Final documentation and demonstration materials

Technology Stack
Python 3.13

Pandas

Streamlit

Pydantic

SQLite

Pytest

Git / GitHub

Project Goal
FoodPulse demonstrates how operational evidence can be converted into transparent reliability priorities while preserving human control, auditability, telemetry safety, and measurable validation.