import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import uuid
from datetime import datetime


# =========================================================
# PROJECT PATH
# =========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from src.decision_engine import evaluate_locality
from src.priority_metrics import (
    calculate_priority_justification
)
from src.event_processor import EventProcessor

# =========================================================
# STREAMLIT PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Food Delivery SLO Decision Dashboard",
    page_icon="🍔",
    layout="wide"
)


# =========================================================
# DATA DIRECTORY
# =========================================================

DATA_DIR = ROOT_DIR / "data"


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    service = pd.read_csv(
        DATA_DIR / "service_metrics.csv"
    )

    weather = pd.read_csv(
        DATA_DIR / "weather.csv"
    )

    support = pd.read_csv(
        DATA_DIR / "support_incidents.csv"
    )

    reliability = pd.read_csv(
        DATA_DIR / "reliability_tasks.csv"
    )

    features = pd.read_csv(
        DATA_DIR / "feature_plans.csv"
    )

    return (
        service,
        weather,
        support,
        reliability,
        features
    )


service, weather, support, reliability, features = load_data()
# =========================================================
# EVENT PROCESSOR
# =========================================================

if "event_processor" not in st.session_state:

    st.session_state.event_processor = EventProcessor(
        allowed_delay_seconds=30
    )

# =========================================================
# PRIORITY JUSTIFICATION METRIC
# =========================================================

priority_metrics = calculate_priority_justification(
    service,
    weather,
    support,
    reliability
)

# =========================================================
# DASHBOARD HEADER
# =========================================================

st.title(
    "🍔 Food Delivery SLO Decision Dashboard"
)

st.markdown(
    """
    **Reliability decisions based on measured user impact,
    SLO performance, error-budget status and
    locality-specific weather conditions.**
    """
)

st.divider()


# =========================================================
# SIDEBAR CONTROLS
# =========================================================

st.sidebar.header("🎛️ Dashboard Controls")

localities = sorted(
    service["locality"].unique()
)

selected_locality = st.sidebar.selectbox(
    "Select Locality",
    localities
)


# =========================================================
# GET SELECTED LOCALITY DATA
# =========================================================

service_rows = service[
    service["locality"] == selected_locality
]

weather_rows = weather[
    weather["locality"] == selected_locality
]

support_rows = support[
    support["locality"] == selected_locality
]


# Get latest service record
service_row = service_rows.iloc[-1]


# Get latest weather record
weather_row = weather_rows.iloc[-1]


# Get latest support record
if len(support_rows) > 0:

    support_row = support_rows.iloc[-1]

else:

    support_row = pd.Series(
        {
            "customer_complaints": 0
        }
    )


# =========================================================
# RUN DECISION ENGINE
# =========================================================

decision = evaluate_locality(
    service_row,
    support_row,
    weather_row
)


# =========================================================
# RELIABILITY STATUS
# =========================================================

st.subheader(
    f"📍 {selected_locality} Reliability Status"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "SLI",
        f"{decision['SLI']}%"
    )


with col2:

    st.metric(
        "SLO Target",
        f"{decision['SLO']}%"
    )


with col3:

    st.metric(
        "Error Budget Remaining",
        f"{decision['error_budget_remaining']}%"
    )


with col4:

    st.metric(
        "User Impact",
        f"{decision['user_impact']}/100"
    )


st.divider()


# =========================================================
# STATUS INDICATORS
# =========================================================

col1, col2, col3 = st.columns(3)


# ---------------------------------------------------------
# SLO STATUS
# ---------------------------------------------------------

with col1:

    if decision["SLI"] < decision["SLO"]:

        st.error(
            "❌ SLO BREACH"
        )

    else:

        st.success(
            "✅ SLO HEALTHY"
        )


# ---------------------------------------------------------
# WEATHER STATUS
# ---------------------------------------------------------

with col2:

    rainfall = decision["rainfall_mm"]

    if rainfall >= 30:

        st.error(
            f"🌧️ Heavy Rain — {rainfall} mm"
        )

    elif rainfall >= 15:

        st.warning(
            f"🌧️ Moderate Rain — {rainfall} mm"
        )

    else:

        st.success(
            f"☀️ Low Weather Risk — {rainfall} mm"
        )


# ---------------------------------------------------------
# PRIORITY STATUS
# ---------------------------------------------------------

with col3:

    priority = decision["priority"]

    if priority.startswith("P1"):

        st.error(
            f"🔴 {priority}"
        )

    elif priority.startswith("P2"):

        st.warning(
            f"🟠 {priority}"
        )

    else:

        st.info(
            f"🟢 {priority}"
        )


st.divider()


# =========================================================
# ENGINEERING RECOMMENDATION
# =========================================================

st.subheader(
    "🤖 Engineering Recommendation"
)

st.info(
    decision["recommendation"]
)


# =========================================================
# EVIDENCE BEHIND RECOMMENDATION
# =========================================================

st.subheader(
    "🔎 Evidence Behind Recommendation"
)


evidence_col1, evidence_col2 = st.columns(2)


# ---------------------------------------------------------
# SERVICE EVIDENCE
# ---------------------------------------------------------

with evidence_col1:

    st.markdown(
        "### 📊 Service Evidence"
    )

    st.write(
        f"**SLI:** {decision['SLI']}%"
    )

    st.write(
        f"**SLO:** {decision['SLO']}%"
    )

    st.write(
        f"**Error Budget Remaining:** "
        f"{decision['error_budget_remaining']}%"
    )

    st.write(
        f"**Total Orders:** "
        f"{service_row['total_orders']}"
    )

    st.write(
        f"**Failed Orders:** "
        f"{service_row['failed_orders']}"
    )

    st.write(
        f"**Average Delivery Time:** "
        f"{service_row['avg_delivery_minutes']} minutes"
    )


# ---------------------------------------------------------
# USER + WEATHER EVIDENCE
# ---------------------------------------------------------

with evidence_col2:

    st.markdown(
        "### 👥 User & Weather Evidence"
    )

    st.write(
        f"**Customer Complaints:** "
        f"{support_row['customer_complaints']}"
    )

    st.write(
        f"**Rainfall:** "
        f"{weather_row['rainfall_mm']} mm"
    )

    st.write(
        f"**Weather Condition:** "
        f"{weather_row['weather_condition']}"
    )

    st.write(
        f"**Priority Score:** "
        f"{decision['priority_score']}"
    )


st.divider()


# =========================================================
# RELIABILITY TASKS
# =========================================================

st.subheader(
    "🛠️ Available Reliability Tasks"
)


locality_tasks = reliability[
    (reliability["locality"] == selected_locality)
    |
    (reliability["locality"] == "All")
]


if len(locality_tasks) > 0:

    st.dataframe(
        locality_tasks[
            [
                "task_id",
                "task_title",
                "service_area",
                "priority",
                "estimated_effort_hours",
                "status"
            ]
        ],
        use_container_width=True
    )

else:

    st.info(
        "No locality-specific reliability tasks found."
    )


st.divider()


# =========================================================
# FEATURE PLANS
# =========================================================

st.subheader(
    "🚀 Competing Feature Plans"
)


feature_display = features[
    (features["locality"] == selected_locality)
    |
    (features["locality"] == "All")
]


if len(feature_display) > 0:

    st.dataframe(
        feature_display[
            [
                "feature_id",
                "feature_name",
                "business_value",
                "engineering_effort",
                "status"
            ]
        ],
        use_container_width=True
    )

else:

    st.info(
        "No feature plans found."
    )


st.divider()


# =========================================================
# DECISION SUMMARY
# =========================================================

st.subheader(
    "📋 Decision Summary"
)


summary = pd.DataFrame(
    {
        "Metric": [
            "Locality",
            "SLI",
            "SLO",
            "Error Budget Remaining",
            "User Impact",
            "Rainfall",
            "Priority Score",
            "Priority"
        ],

        "Value": [
            decision["locality"],
            f"{decision['SLI']}%",
            f"{decision['SLO']}%",
            f"{decision['error_budget_remaining']}%",
            decision["user_impact"],
            f"{decision['rainfall_mm']} mm",
            decision["priority_score"],
            decision["priority"]
        ]
    }
)


st.table(summary)


# =========================================================
# HUMAN DECISION + MANUAL OVERRIDE
# =========================================================

st.divider()

st.subheader(
    "👤 Human Decision"
)

st.write(
    """
    The system provides an engineering recommendation,
    but the final decision remains with a human stakeholder.
    High-impact reliability decisions require human confirmation.
    """
)


# =========================================================
# SHOW CURRENT RECOMMENDATION
# =========================================================

st.markdown(
    "### 🤖 System Recommendation"
)

st.info(
    f"**{decision['priority']}**\n\n"
    f"{decision['recommendation']}"
)


# =========================================================
# HUMAN DECISION OPTION
# =========================================================

decision_choice = st.radio(
    "Choose an action:",
    [
        "Approve Recommendation",
        "Override Recommendation"
    ]
)


# =========================================================
# OVERRIDE REASON
# =========================================================

override_reason = ""


if decision_choice == "Override Recommendation":

    st.warning(
        "⚠️ You are overriding the system recommendation."
    )

    override_reason = st.text_area(
        "Reason for override (required):",
        placeholder=(
            "Explain why the recommended action is being overridden."
        )
    )

    if override_reason.strip() == "":

        st.warning(
            "⚠️ Please provide an override reason before submitting."
        )


# =========================================================
# SUBMIT DECISION
# =========================================================

if st.button(
    "Submit Decision",
    type="primary"
):

    # -----------------------------------------------------
    # VALIDATE OVERRIDE
    # -----------------------------------------------------

    if (
        decision_choice == "Override Recommendation"
        and override_reason.strip() == ""
    ):

        st.error(
            "❌ Override reason is required."
        )


    else:

        # -------------------------------------------------
        # GENERATE UNIQUE DECISION ID
        # -------------------------------------------------

        decision_id = str(
            uuid.uuid4()
        )


        # -------------------------------------------------
        # GENERATE TIMESTAMP
        # -------------------------------------------------

        timestamp = datetime.now().isoformat()


        # -------------------------------------------------
        # CREATE AUDIT RECORD
        # -------------------------------------------------

        audit_record = pd.DataFrame(
            [
                {
                    "decision_id": decision_id,

                    "timestamp": timestamp,

                    "locality": decision["locality"],

                    "recommended_priority":
                        decision["priority"],

                    "recommended_action":
                        decision["recommendation"],

                    "decision":
                        decision_choice,

                    "override_reason":
                        override_reason,

                    "priority_score":
                        decision["priority_score"],

                    "sli":
                        decision["SLI"],

                    "slo":
                        decision["SLO"],

                    "user_impact":
                        decision["user_impact"],

                    "rainfall_mm":
                        decision["rainfall_mm"]
                }
            ]
        )


        # -------------------------------------------------
        # AUDIT FILE
        # -------------------------------------------------

        audit_file = (
            DATA_DIR / "decision_audit.csv"
        )


        # -------------------------------------------------
        # SAVE AUDIT RECORD
        # -------------------------------------------------

        audit_record.to_csv(
            audit_file,
            mode="a",
            header=False,
            index=False
        )


        # -------------------------------------------------
        # SUCCESS MESSAGE
        # -------------------------------------------------

        st.success(
            "✅ Decision recorded successfully!"
        )


        st.write(
            f"**Decision ID:** `{decision_id}`"
        )

        st.write(
            f"**Decision:** {decision_choice}"
        )

        if decision_choice == "Override Recommendation":

            st.write(
                f"**Override Reason:** {override_reason}"
            )


# =========================================================
# AUDIT TRAIL VIEWER
# =========================================================

st.divider()

st.subheader(
    "📜 Decision Audit Trail"
)


audit_file = (
    DATA_DIR / "decision_audit.csv"
)


if audit_file.exists():

    try:

        audit_data = pd.read_csv(
            audit_file
        )

        if len(audit_data) > 0:

            st.dataframe(
                audit_data,
                use_container_width=True
            )

        else:

            st.info(
                "No decisions have been recorded yet."
            )

    except Exception as e:

        st.error(
            f"Unable to read audit trail: {e}"
        )

else:

    st.info(
        "No audit file found. "
        "Submit a decision to create the audit trail."
    )


# =========================================================
# END OF DASHBOARD
# =========================================================

# =========================================================
# MEASURABLE EXPERIMENT
# =========================================================

st.divider()

st.subheader(
    "📈 Reliability Priority Justification"
)

st.write(
    """
    This metric measures the percentage of reliability
    priorities supported by measured service and user-impact
    evidence.
    """
)


# ---------------------------------------------------------
# BASELINE / TARGET / CURRENT RESULT
# ---------------------------------------------------------

BASELINE = 0.0
TARGET = 80.0

CURRENT_RESULT = priority_metrics[
    "justification_percentage"
]

IMPROVEMENT = (
    CURRENT_RESULT - BASELINE
)


metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)


with metric_col1:

    st.metric(
        "Baseline",
        f"{BASELINE}%"
    )


with metric_col2:

    st.metric(
        "Target",
        f"{TARGET}%"
    )


with metric_col3:

    st.metric(
        "Measured Result",
        f"{CURRENT_RESULT}%"
    )


with metric_col4:

    st.metric(
        "Improvement",
        f"+{IMPROVEMENT:.2f} pp"
    )


# ---------------------------------------------------------
# TARGET STATUS
# ---------------------------------------------------------

if CURRENT_RESULT >= TARGET:

    st.success(
        "✅ Target achieved: reliability priorities "
        "are sufficiently supported by measured evidence."
    )

else:

    st.warning(
        "⚠️ Target not yet achieved. "
        "More reliability priorities need measurable evidence."
    )


# ---------------------------------------------------------
# EXPERIMENT DETAILS
# ---------------------------------------------------------

st.markdown(
    "### 🧪 Experiment Definition"
)

st.write(
    """
    **Baseline:** Reliability tasks are evaluated without
    an explicit measured user-impact justification.

    **Target:** At least 80% of reliability priorities should
    be supported by measured evidence.

    **Measured result:** Calculated using SLI, SLO,
    error-budget status and user-impact measurements.

    **Justification rule:** A reliability priority is considered
    justified when at least one significant measured risk exists:
    SLO breach, high user impact, or low remaining error budget.
    """
)


# ---------------------------------------------------------
# DETAILED RESULTS
# ---------------------------------------------------------

st.markdown(
    "### 🔎 Priority Justification Details"
)

details = priority_metrics["details"]


if len(details) > 0:

    st.dataframe(
        details,
        use_container_width=True
    )

else:

    st.info(
        "No reliability priority data available."
    )


# ---------------------------------------------------------
# ERROR ANALYSIS
# ---------------------------------------------------------

st.markdown(
    "### ⚠️ Error Analysis"
)

if len(details) > 0:

    unjustified = details[
        details["justified"] == False
    ]

    if len(unjustified) == 0:

        st.success(
            "No unjustified reliability priorities "
            "were found in the current validation dataset."
        )

    else:

        st.warning(
            f"{len(unjustified)} reliability priorities "
            "do not currently have sufficient measured evidence."
        )

        st.dataframe(
            unjustified[
                [
                    "task_id",
                    "task_title",
                    "locality",
                    "task_priority",
                    "SLI",
                    "user_impact",
                    "error_budget_remaining"
                ]
            ],
            use_container_width=True
        )
        # =========================================================
# EVENT RELIABILITY SIMULATOR
# =========================================================

st.divider()

st.subheader(
    "⚡ Event Reliability Simulator"
)

st.write(
    """
    Simulate real-world event delivery problems such as
    duplicate, delayed and out-of-order events. The processor
    protects the current order state from invalid updates.
    """
)


# =========================================================
# GET EVENT PROCESSOR
# =========================================================

processor = st.session_state.event_processor


# =========================================================
# EVENT CREATION FUNCTION
# =========================================================

def create_event(
    event_id,
    order_id,
    event_time,
    status
):

    return {
        "event_id": event_id,
        "order_id": order_id,
        "event_time": event_time,
        "status": status
    }


# =========================================================
# SIMULATION BUTTONS
# =========================================================

st.markdown(
    "### 🧪 Failure Scenario Tests"
)


col1, col2, col3, col4 = st.columns(4)


# ---------------------------------------------------------
# NORMAL EVENT
# ---------------------------------------------------------

with col1:

    if st.button(
        "🔵 Normal Event"
    ):

        event = create_event(
            "SIM001",
            "ORDER001",
            "2026-09-07T10:00:00",
            "PLACED"
        )

        result = processor.process_event(
            event
        )

        st.session_state.last_event_result = result


# ---------------------------------------------------------
# DUPLICATE EVENT
# ---------------------------------------------------------

with col2:

    if st.button(
        "🔴 Duplicate Event"
    ):

        event = create_event(
            "SIM001",
            "ORDER001",
            "2026-09-07T10:00:00",
            "PLACED"
        )

        result = processor.process_event(
            event
        )

        st.session_state.last_event_result = result


# ---------------------------------------------------------
# OUT-OF-ORDER EVENT
# ---------------------------------------------------------

with col3:

    if st.button(
        "🟣 Out-of-Order"
    ):

        event = create_event(
            "SIM002",
            "ORDER001",
            "2026-09-07T09:59:00",
            "ACCEPTED"
        )

        result = processor.process_event(
            event
        )

        st.session_state.last_event_result = result


# ---------------------------------------------------------
# DELAYED EVENT
# ---------------------------------------------------------

with col4:

    if st.button(
        "🟠 Delayed Event"
    ):

        event = create_event(
            "SIM003",
            "ORDER002",
            "2026-09-07T09:00:00",
            "PLACED"
        )

        result = processor.process_event(
            event
        )

        st.session_state.last_event_result = result


# =========================================================
# DISPLAY LAST EVENT RESULT
# =========================================================

if "last_event_result" in st.session_state:

    result = st.session_state.last_event_result

    st.markdown(
        "### 📡 Latest Event Result"
    )

    if result["status"] == "processed":

        st.success(
            f"✅ {result['message']}"
        )

    elif result["status"] == "duplicate":

        st.error(
            "🔴 Duplicate event detected and ignored."
        )

    elif result["status"] == "out_of_order":

        st.warning(
            "🟣 Out-of-order event detected. "
            "Existing newer state was protected."
        )

    elif result["status"] == "delayed":

        st.warning(
            "🟠 Delayed event detected and safely processed."
        )

    st.json(result)


# =========================================================
# CURRENT ORDER STATE
# =========================================================

st.markdown(
    "### 📦 Current Order State"
)


if len(processor.order_state) > 0:

    state_rows = []

    for order_id, state in processor.order_state.items():

        state_rows.append(
            {
                "Order ID": order_id,
                "Current Status": state["status"],
                "Latest Event Time":
                    state["event_time"].isoformat()
            }
        )

    state_df = pd.DataFrame(
        state_rows
    )

    st.dataframe(
        state_df,
        use_container_width=True
    )

else:

    st.info(
        "No events have been processed yet."
    )


# =========================================================
# EVENT PROCESSING STATISTICS
# =========================================================

st.markdown(
    "### 📊 Event Processing Statistics"
)


stats = processor.get_statistics()


stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)


with stat_col1:

    st.metric(
        "Processed",
        stats["processed"]
    )


with stat_col2:

    st.metric(
        "Duplicates",
        stats["duplicates"]
    )


with stat_col3:

    st.metric(
        "Delayed",
        stats["delayed"]
    )


with stat_col4:

    st.metric(
        "Out-of-Order",
        stats["out_of_order"]
    )


# =========================================================
# RECOVERY TEST
# =========================================================

st.markdown(
    "### 🔄 Recovery Demonstration"
)

st.write(
    """
    The recovery test sends a sequence containing normal,
    duplicate and out-of-order events. The final state should
    remain consistent with the newest valid event.
    """
)


if st.button(
    "🟢 Run Recovery Test"
):

    recovery_processor = EventProcessor(
        allowed_delay_seconds=30
    )

    recovery_events = [

        create_event(
            "R001",
            "RECOVERY001",
            "2026-09-07T10:00:00",
            "PLACED"
        ),

        create_event(
            "R002",
            "RECOVERY001",
            "2026-09-07T10:00:10",
            "ACCEPTED"
        ),

        # Out-of-order event
        create_event(
            "R003",
            "RECOVERY001",
            "2026-09-07T10:00:05",
            "PLACED"
        ),

        # Duplicate event
        create_event(
            "R002",
            "RECOVERY001",
            "2026-09-07T10:00:10",
            "ACCEPTED"
        ),

        # New valid event
        create_event(
            "R004",
            "RECOVERY001",
            "2026-09-07T10:00:20",
            "PICKED_UP"
        )
    ]


    recovery_results = []

    for event in recovery_events:

        result = recovery_processor.process_event(
            event
        )

        recovery_results.append(
            {
                "Event ID": event["event_id"],
                "Status": result["status"],
                "Event State": event["status"]
            }
        )


    st.dataframe(
        pd.DataFrame(recovery_results),
        use_container_width=True
    )


    final_state = recovery_processor.get_order_state(
        "RECOVERY001"
    )


    st.success(
        f"✅ Recovery successful. "
        f"Final order state: {final_state['status']}"
    )

    st.write(
        "Expected final state: **PICKED_UP**"
    )