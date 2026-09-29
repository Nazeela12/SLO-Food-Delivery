import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import sys


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.decision_engine import evaluate_locality
from src.priority_metrics import calculate_priority_justification
from src.event_processor import EventProcessor
from src.audit_store import AuditStore
from src.sensitivity_analysis import run_sensitivity_analysis
from src.sensitivity_analysis import calculate_priority_stability


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="FoodPulse | SLO Decision Center",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SIMPLE NATIVE UI STYLING
# ============================================================

# IMPORTANT:
# This dashboard does NOT depend on HTML rendering.
# All visible components below use native Streamlit widgets.

st.title("FoodPulse Reliability Console")

st.caption(
    "Locality-aware SLO decision support for food-delivery reliability operations."
)

st.divider()


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_data():

    service = pd.read_csv(DATA_DIR / "service_metrics.csv")
    support = pd.read_csv(DATA_DIR / "support_incidents.csv")
    weather = pd.read_csv(DATA_DIR / "weather.csv")
    reliability = pd.read_csv(DATA_DIR / "reliability_tasks.csv")
    features = pd.read_csv(DATA_DIR / "feature_plans.csv")

    return service, support, weather, reliability, features


service, support, weather, reliability, features = load_data()


# ============================================================
# SQLITE AUDIT
# ============================================================

DB_PATH = DATA_DIR / "decision_audit.db"
audit_store = AuditStore(DB_PATH)


# ============================================================
# OPTIONAL LEGACY CSV MIGRATION
# ============================================================

def migrate_old_audit_if_needed():

    csv_path = DATA_DIR / "decision_audit.csv"

    if not csv_path.exists():
        return

    try:

        existing = audit_store.get_all_decisions()

        if len(existing) > 0:
            return

        old_data = pd.read_csv(csv_path)

        if len(old_data) == 0:
            return

        required_columns = [
            "decision_id",
            "timestamp",
            "locality",
            "recommended_priority",
            "recommended_action",
            "decision",
            "override_reason",
            "priority_score",
            "sli",
            "slo",
            "user_impact",
            "rainfall_mm"
        ]

        if all(column in old_data.columns for column in required_columns):

            for _, row in old_data.iterrows():

                record = {
                    "decision_id": str(row["decision_id"]),
                    "timestamp": str(row["timestamp"]),
                    "locality": str(row["locality"]),
                    "recommended_priority": str(
                        row["recommended_priority"]
                    ),
                    "recommended_action": str(
                        row["recommended_action"]
                    ),
                    "decision": str(row["decision"]),
                    "override_reason": str(
                        row["override_reason"]
                    ),
                    "priority_score": float(
                        row["priority_score"]
                    ),
                    "sli": float(row["sli"]),
                    "slo": float(row["slo"]),
                    "user_impact": float(
                        row["user_impact"]
                    ),
                    "rainfall_mm": float(
                        row["rainfall_mm"]
                    )
                }

                try:
                    audit_store.save_decision(record)
                except Exception:
                    pass

    except Exception:
        pass


migrate_old_audit_if_needed()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_number(value, decimals=2):

    try:
        return round(float(value), decimals)
    except Exception:
        return 0


def find_locality_rows(locality):

    service_rows = service[
        service["locality"] == locality
    ]

    weather_rows = weather[
        weather["locality"] == locality
    ]

    support_rows = support[
        support["locality"] == locality
    ]

    if len(service_rows) == 0:
        return None, None, None

    service_row = service_rows.iloc[-1]

    if len(weather_rows) > 0:
        weather_row = weather_rows.iloc[-1]
    else:
        weather_row = pd.Series({
            "rainfall_mm": 0
        })

    if len(support_rows) > 0:
        support_row = support_rows.iloc[-1]
    else:
        support_row = pd.Series({
            "customer_complaints": 0
        })

    return service_row, support_row, weather_row


def get_priority_message(priority):

    if "P1" in str(priority):
        return "🔴 Critical"

    if "P2" in str(priority):
        return "🟠 High"

    if "P3" in str(priority):
        return "🔵 Medium"

    return "🟢 Low"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("FOODPULSE")

    st.caption(
        "SLO Decision & Reliability Console"
    )

    st.divider()

    st.subheader("Operations Control")

    localities = sorted(
        service["locality"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_locality = st.selectbox(
        "Monitor locality",
        localities,
        index=0
    )

    st.divider()

    st.subheader("Data Sources")

    st.write("✓ Service telemetry")
    st.write("✓ Support incidents")
    st.write("✓ Weather conditions")
    st.write("✓ Reliability tasks")
    st.write("✓ Feature plans")
    st.write("✓ SQLite audit log")

    st.divider()

    st.subheader("System Status")

    st.success("SYSTEM ONLINE")

    st.write("Decision engine: ACTIVE")
    st.write("Audit persistence: SQLITE")
    st.write("Event recovery: ENABLED")
    st.write("Human approval: REQUIRED")

    st.divider()

    st.caption(
        "Evaluation time: "
        + datetime.now().strftime(
            "%d %b %Y, %H:%M"
        )
    )


# ============================================================
# CURRENT DECISION
# ============================================================

service_row, support_row, weather_row = find_locality_rows(
    selected_locality
)


if service_row is None:

    st.error(
        f"No service telemetry found for {selected_locality}."
    )

    st.stop()


decision = evaluate_locality(
    service_row,
    support_row,
    weather_row
)


# ============================================================
# SYSTEM STATUS BANNER
# ============================================================

status_col1, status_col2, status_col3, status_col4 = st.columns(4)

with status_col1:
    st.success("SYSTEM OPERATIONAL")

with status_col2:
    st.info("LIVE DECISION DATA")

with status_col3:
    st.info("SQLITE AUDIT ENABLED")

with status_col4:
    st.info("HUMAN-IN-THE-LOOP")


# ============================================================
# TABS
# ============================================================

(
    tab_overview,
    tab_evidence,
    tab_governance,
    tab_validation,
    tab_reliability
) = st.tabs(
    [
        "Overview",
        "Evidence & Work",
        "Governance & Audit",
        "Validation",
        "Reliability Tests"
    ]
)


# ============================================================
# TAB 1 — OVERVIEW
# ============================================================

with tab_overview:

    st.header(
        f"{selected_locality} Reliability Status"
    )

    st.caption(
        "Current operational view based on service performance, "
        "user impact, error budget and weather conditions."
    )

    # --------------------------------------------------------
    # KPI ROW
    # --------------------------------------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.metric(
            "Service SLI",
            f'{decision["SLI"]:.2f}%',
            f'SLO {decision["SLO"]:.0f}%'
        )

    with col2:

        st.metric(
            "Error Budget",
            f'{decision["error_budget_remaining"]:.2f}%',
            "remaining"
        )

    with col3:

        st.metric(
            "User Impact",
            f'{decision["user_impact"]:.2f}',
            "impact score"
        )

    with col4:

        st.metric(
            "Priority Score",
            f'{decision["priority_score"]:.2f}',
            decision["priority"]
        )

    with col5:

        st.metric(
            "Rainfall",
            f'{decision["rainfall_mm"]:.1f} mm',
            "weather factor"
        )

    st.divider()

    # --------------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------------

    col_left, col_right = st.columns(
        [1.4, 1]
    )

    with col_left:

        st.subheader(
            "Decision Engine Recommendation"
        )

        priority_display = get_priority_message(
            decision["priority"]
        )

        st.info(
            f"Priority: **{priority_display}**"
        )

        st.write(
            decision["recommendation"]
        )

        st.caption(
            "The recommendation is generated from measured "
            "operational evidence and requires human confirmation."
        )

    with col_right:

        st.subheader("Decision Inputs")

        input_data = pd.DataFrame(
            {
                "Input": [
                    "Locality",
                    "SLO Target",
                    "Service SLI",
                    "Customer Complaints",
                    "Failed Orders",
                    "Rainfall"
                ],
                "Value": [
                    selected_locality,
                    f'{decision["SLO"]:.0f}%',
                    f'{decision["SLI"]:.2f}%',
                    safe_number(
                        support_row.get(
                            "customer_complaints",
                            0
                        )
                    ),
                    safe_number(
                        service_row.get(
                            "failed_orders",
                            0
                        )
                    ),
                    f'{decision["rainfall_mm"]:.1f} mm'
                ]
            }
        )

        st.dataframe(
            input_data,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # DECISION LOGIC
    # --------------------------------------------------------

    st.divider()

    st.subheader("Decision Logic")

    st.write(
        "The priority score combines **SLO risk, user impact, "
        "error-budget risk and weather conditions**."
    )

    st.write(
        "**Weighting:** 40% SLO risk + 35% user impact + "
        "15% error-budget risk + 10% weather."
    )

    logic1, logic2, logic3, logic4 = st.columns(4)

    with logic1:

        st.info(
            f"**SLO Risk**\n\n"
            f"SLI: {decision['SLI']:.2f}%\n\n"
            f"Target: {decision['SLO']:.0f}%"
        )

    with logic2:

        st.info(
            f"**User Impact**\n\n"
            f"Score: {decision['user_impact']:.2f}"
        )

    with logic3:

        st.info(
            f"**Error Budget**\n\n"
            f"Remaining: "
            f"{decision['error_budget_remaining']:.2f}%"
        )

    with logic4:

        st.info(
            f"**Weather**\n\n"
            f"Rainfall: "
            f"{decision['rainfall_mm']:.1f} mm"
        )

    # --------------------------------------------------------
    # QUICK INTERPRETATION
    # --------------------------------------------------------

    st.divider()

    st.subheader("Operational Interpretation")

    if decision["priority"].startswith("P1"):

        st.error(
            "Critical reliability condition detected. "
            "The measured evidence indicates immediate attention."
        )

    elif decision["priority"].startswith("P2"):

        st.warning(
            "High reliability priority detected. "
            "The evidence supports scheduling reliability work."
        )

    elif decision["priority"].startswith("P3"):

        st.info(
            "Medium reliability priority detected. "
            "The locality should be monitored and improvement work "
            "can be scheduled according to capacity."
        )

    else:

        st.success(
            "Low immediate reliability risk detected. "
            "No immediate intervention is indicated by the current evidence."
        )


# ============================================================
# TAB 2 — EVIDENCE & WORK
# ============================================================

with tab_evidence:

    st.header(
        "Operational Evidence & Engineering Work"
    )

    st.caption(
        "Evidence chain connecting telemetry to reliability tasks "
        "and feature planning."
    )

    evidence1, evidence2 = st.columns(2)

    # --------------------------------------------------------
    # SERVICE TELEMETRY
    # --------------------------------------------------------

    with evidence1:

        st.subheader("Service Telemetry")

        service_display = pd.DataFrame(
            [service_row]
        )

        st.dataframe(
            service_display,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Support Evidence")

        support_display = pd.DataFrame(
            [support_row]
        )

        st.dataframe(
            support_display,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # WEATHER + RELIABILITY
    # --------------------------------------------------------

    with evidence2:

        st.subheader("Weather Evidence")

        weather_display = pd.DataFrame(
            [weather_row]
        )

        st.dataframe(
            weather_display,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Reliability Work")

        reliability_locality = reliability[
            reliability["locality"] == selected_locality
        ]

        if len(reliability_locality) == 0:

            st.info(
                "No locality-specific reliability tasks found."
            )

        else:

            st.dataframe(
                reliability_locality,
                use_container_width=True,
                hide_index=True
            )

    # --------------------------------------------------------
    # FEATURE PLANS
    # --------------------------------------------------------

    st.divider()

    st.subheader("Feature Plans")

    feature_locality = features[
        features["locality"]
        .astype(str)
        .str.lower()
        .isin(
            [
                selected_locality.lower(),
                "all"
            ]
        )
    ]

    if len(feature_locality) > 0:

        st.dataframe(
            feature_locality,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No matching feature plans found."
        )


# ============================================================
# TAB 3 — GOVERNANCE & AUDIT
# ============================================================

with tab_governance:

    st.header(
        "Decision Approval & Audit Trail"
    )

    st.caption(
        "Human-in-the-loop governance with persistent SQLite audit storage."
    )

    st.info(
        "The decision engine provides a recommendation. "
        "A human operator must approve, reject or override the recommendation. "
        "Every saved decision is persisted in SQLite for traceability."
    )

    # --------------------------------------------------------
    # CURRENT RECOMMENDATION
    # --------------------------------------------------------

    st.subheader("Current Recommendation")

    rec1, rec2, rec3 = st.columns(3)

    with rec1:

        st.metric(
            "Locality",
            selected_locality
        )

    with rec2:

        st.metric(
            "Recommended Priority",
            decision["priority"]
        )

    with rec3:

        st.metric(
            "Priority Score",
            f'{decision["priority_score"]:.2f}'
        )

    st.write(
        "**Recommendation:**"
    )

    st.write(
        decision["recommendation"]
    )

    st.divider()

    # --------------------------------------------------------
    # HUMAN DECISION
    # --------------------------------------------------------

    st.subheader("Human Decision")

    decision_choice = st.radio(
        "Select operator decision",
        [
            "Approved",
            "Rejected",
            "Overridden"
        ],
        horizontal=True
    )

    override_reason = ""

    if decision_choice == "Overridden":

        override_reason = st.text_area(
            "Reason for override",
            placeholder=(
                "Example: Incident already mitigated; "
                "reliability work deferred to next sprint."
            )
        )

    save_decision = st.button(
        "Save Decision to Audit Log",
        type="primary"
    )

    if save_decision:

        if (
            decision_choice == "Overridden"
            and not override_reason.strip()
        ):

            st.warning(
                "Please provide an override reason before saving."
            )

        else:

            decision_id = (
                "DEC-"
                + datetime.now().strftime(
                    "%Y%m%d%H%M%S%f"
                )
            )

            record = {
                "decision_id": decision_id,
                "timestamp": datetime.now().isoformat(
                    timespec="seconds"
                ),
                "locality": selected_locality,
                "recommended_priority": decision["priority"],
                "recommended_action": decision["recommendation"],
                "decision": decision_choice,
                "override_reason": override_reason,
                "priority_score": float(
                    decision["priority_score"]
                ),
                "sli": float(
                    decision["SLI"]
                ),
                "slo": float(
                    decision["SLO"]
                ),
                "user_impact": float(
                    decision["user_impact"]
                ),
                "rainfall_mm": float(
                    decision["rainfall_mm"]
                )
            }

            try:

                audit_store.save_decision(
                    record
                )

                st.success(
                    f"Decision {decision_id} successfully "
                    f"saved to SQLite."
                )

            except Exception as error:

                st.error(
                    f"Unable to save decision: {error}"
                )

    # --------------------------------------------------------
    # AUDIT HISTORY
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "SQLite Audit History"
    )

    try:

        audit_data = audit_store.get_all_decisions()

        if len(audit_data) == 0:

            st.info(
                "No decisions have been recorded yet."
            )

        else:

            st.dataframe(
                audit_data,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"{len(audit_data)} audited decision(s) "
                "stored in SQLite."
            )

    except Exception as error:

        st.error(
            f"Unable to read SQLite audit history: {error}"
        )


# ============================================================
# TAB 4 — VALIDATION
# ============================================================

with tab_validation:

    st.header(
        "Reliability Priority Justification"
    )

    st.caption(
        "Measured validation of whether reliability priorities "
        "are supported by operational evidence."
    )

    st.write(
        "This experiment measures how often reliability priorities "
        "are supported by measured operational evidence."
    )

    try:

        # --------------------------------------------------------
        # EXISTING JUSTIFICATION EXPERIMENT
        # --------------------------------------------------------

        experiment = calculate_priority_justification(
            service,
            weather,
            support,
            reliability
        )

        total = experiment[
            "total_priorities"
        ]

        justified = experiment[
            "justified_priorities"
        ]

        percentage = experiment[
            "justification_percentage"
        ]

        baseline = 0

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            st.metric(
                "Reliability Priorities",
                total
            )

        with c2:

            st.metric(
                "Evidence-Justified",
                justified
            )

        with c3:

            st.metric(
                "Justification Rate",
                f"{percentage:.2f}%"
            )

        with c4:

            st.metric(
                "Baseline",
                f"{baseline}%"
            )

        st.divider()

        # --------------------------------------------------------
        # EXPERIMENT INTERPRETATION
        # --------------------------------------------------------

        st.subheader(
            "Experiment Interpretation"
        )

        st.write(
            f"Measured justification rate: "
            f"**{percentage:.2f}%**."
        )

        st.write(
            "A priority is considered justified when at least one "
            "measurable condition indicates operational need: "
            "an SLO breach, high user impact, or low remaining "
            "error budget."
        )

        if total > 0:

            st.progress(
                min(
                    percentage / 100,
                    1.0
                )
            )

        st.divider()

        # --------------------------------------------------------
        # PRIORITY EVIDENCE DETAILS
        # --------------------------------------------------------

        st.subheader(
            "Priority Evidence Details"
        )

        details = experiment[
            "details"
        ]

        if len(details) > 0:

            st.dataframe(
                details,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No reliability priority records available."
            )

        st.divider()

        # ========================================================
        # SENSITIVITY ANALYSIS
        # ========================================================

        st.header(
            "Decision Weight Sensitivity Analysis"
        )

        st.caption(
            "Tests how changes in decision-engine weighting "
            "coefficients affect the reliability priority score."
        )

        st.write(
            "The baseline decision model uses four evidence "
            "dimensions: SLO risk, user impact, error-budget risk, "
            "and weather conditions."
        )

        # --------------------------------------------------------
        # BASELINE WEIGHTS
        # --------------------------------------------------------

        st.subheader(
            "Baseline Decision Weights"
        )

        weight_col1, weight_col2, weight_col3, weight_col4 = (
            st.columns(4)
        )

        with weight_col1:

            st.metric(
                "SLO Risk",
                "40%"
            )

        with weight_col2:

            st.metric(
                "User Impact",
                "35%"
            )

        with weight_col3:

            st.metric(
                "Error Budget",
                "15%"
            )

        with weight_col4:

            st.metric(
                "Weather",
                "10%"
            )

        st.info(
            "The sensitivity experiment changes one or more "
            "weighting coefficients while keeping the total "
            "weight equal to 100%."
        )

        # --------------------------------------------------------
        # RUN SENSITIVITY ANALYSIS
        # --------------------------------------------------------

        if len(service) > 0:

            # Use the locality selected in the sidebar.
            selected_service_rows = service[
                service["locality"] == selected_locality
            ]
            selected_weather_rows = weather[
                weather["locality"] == selected_locality
            ]

            selected_support_rows = support[
                support["locality"] == selected_locality
            ]

            if len(selected_service_rows) > 0:

                service_row = selected_service_rows.iloc[-1]

            else:

                service_row = service.iloc[-1]

            if len(selected_weather_rows) > 0:

                weather_row = selected_weather_rows.iloc[-1]

            else:

                weather_row = weather.iloc[-1]

            if len(selected_support_rows) > 0:

                support_row = selected_support_rows.iloc[-1]

            else:

                support_row = pd.Series(
                    {
                        "customer_complaints": 0
                    }
                )

            sensitivity_results = run_sensitivity_analysis(
                service_row,
                support_row,
                weather_row
            )

            stability = calculate_priority_stability(
                sensitivity_results
            )

            # ----------------------------------------------------
            # SENSITIVITY KPI
            # ----------------------------------------------------

            st.subheader(
                "Sensitivity Result"
            )

            sc1, sc2, sc3 = st.columns(3)

            with sc1:

                st.metric(
                    "Scenarios Tested",
                    len(sensitivity_results)
                )

            with sc2:

                st.metric(
                    "Baseline Priority",
                    sensitivity_results.iloc[0]["priority"]
                )

            with sc3:

                st.metric(
                    "Priority Stability",
                    f"{stability:.2f}%"
                )

            st.write(
                f"**Locality analysed:** {selected_locality}"
            )

            st.write(
                "Priority stability measures how often the "
                "priority classification remains the same as "
                "the baseline when the weighting coefficients "
                "are changed."
            )

            # ----------------------------------------------------
            # SENSITIVITY TABLE
            # ----------------------------------------------------

            st.subheader(
                "Weighting Scenario Comparison"
            )

            display_results = sensitivity_results.copy()

            display_results[
                "slo_weight"
            ] = (
                display_results["slo_weight"] * 100
            ).round(0).astype(int).astype(str) + "%"

            display_results[
                "user_impact_weight"
            ] = (
                display_results["user_impact_weight"] * 100
            ).round(0).astype(int).astype(str) + "%"

            display_results[
                "error_budget_weight"
            ] = (
                display_results["error_budget_weight"] * 100
            ).round(0).astype(int).astype(str) + "%"

            display_results[
                "weather_weight"
            ] = (
                display_results["weather_weight"] * 100
            ).round(0).astype(int).astype(str) + "%"

            display_results = display_results.rename(
                columns={
                    "scenario": "Scenario",
                    "slo_weight": "SLO Risk",
                    "user_impact_weight": "User Impact",
                    "error_budget_weight": "Error Budget",
                    "weather_weight": "Weather",
                    "priority_score": "Priority Score",
                    "priority": "Priority"
                }
            )

            st.dataframe(
                display_results[
                    [
                        "Scenario",
                        "SLO Risk",
                        "User Impact",
                        "Error Budget",
                        "Weather",
                        "Priority Score",
                        "Priority"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )

            # ----------------------------------------------------
            # INTERPRETATION
            # ----------------------------------------------------

            st.subheader(
                "Sensitivity Interpretation"
            )

            baseline_score = sensitivity_results.iloc[0][
                "priority_score"
            ]

            minimum_score = sensitivity_results[
                "priority_score"
            ].min()

            maximum_score = sensitivity_results[
                "priority_score"
            ].max()

            st.write(
                f"The baseline priority score is "
                f"**{baseline_score:.2f}**."
            )

            st.write(
                f"Across the tested weighting scenarios, "
                f"the priority score ranges from "
                f"**{minimum_score:.2f}** to "
                f"**{maximum_score:.2f}**."
            )

            st.write(
                f"The priority classification matched the "
                f"baseline in **{stability:.2f}%** of the "
                f"tested scenarios."
            )

            st.caption(
                "This sensitivity analysis is an experiment, "
                "not a claim that one weighting scheme is "
                "universally correct."
            )

        else:

            st.info(
                "Sensitivity analysis requires available "
                "service telemetry data."
            )

    except Exception as error:

        st.error(
            "Validation experiment could not be calculated: "
            + str(error)
        )


# ============================================================
# TAB 5 — RELIABILITY TESTS
# ============================================================

with tab_reliability:

    st.header(
        "Telemetry Event Recovery Tests"
    )

    st.caption(
        "Tests protection against duplicate, delayed and "
        "out-of-order telemetry events."
    )

    st.write(
        "The event processor protects order state from duplicate, "
        "delayed and out-of-order telemetry events."
    )

    # --------------------------------------------------------
    # TEST CASE SUMMARY
    # --------------------------------------------------------

    test1, test2, test3 = st.columns(3)

    with test1:

        st.info(
            "**Duplicate Events**\n\n"
            "The same event_id is received again.\n\n"
            "Expected: ignore duplicate."
        )

    with test2:

        st.info(
            "**Out-of-Order Events**\n\n"
            "An older timestamp arrives after a newer event.\n\n"
            "Expected: preserve newer state."
        )

    with test3:

        st.info(
            "**Delayed Events**\n\n"
            "An event arrives significantly later.\n\n"
            "Expected: detect delay safely."
        )

    st.divider()

    # --------------------------------------------------------
    # RUN TEST
    # --------------------------------------------------------

    if st.button(
        "Run Recovery Test",
        type="primary"
    ):

        processor = EventProcessor(
            allowed_delay_seconds=30
        )

        base_time = datetime.now().replace(
            microsecond=0
        )

        test_events = [

            {
                "event_id": "EVT-001",
                "order_id": "ORD-1001",
                "event_time": base_time.isoformat(),
                "status": "PLACED"
            },

            {
                "event_id": "EVT-002",
                "order_id": "ORD-1001",
                "event_time": (
                    base_time
                    + timedelta(seconds=10)
                ).isoformat(),
                "status": "PREPARING"
            },

            {
                "event_id": "EVT-003",
                "order_id": "ORD-1001",
                "event_time": (
                    base_time
                    + timedelta(seconds=5)
                ).isoformat(),
                "status": "CONFIRMED"
            },

            {
                "event_id": "EVT-004",
                "order_id": "ORD-1001",
                "event_time": (
                    base_time
                    - timedelta(seconds=60)
                ).isoformat(),
                "status": "PLACED"
            },

            {
                "event_id": "EVT-002",
                "order_id": "ORD-1001",
                "event_time": (
                    base_time
                    + timedelta(seconds=10)
                ).isoformat(),
                "status": "PREPARING"
            }
        ]

        results = []

        for event in test_events:

            result = processor.process_event(
                event
            )

            results.append(
                {
                    "Event": event["event_id"],
                    "Result": result["status"],
                    "Message": result["message"]
                }
            )

        st.subheader(
            "Event Processing Results"
        )

        st.dataframe(
            pd.DataFrame(results),
            use_container_width=True,
            hide_index=True
        )

        st.subheader(
            "Processor Statistics"
        )

        stats = processor.get_statistics()

        s1, s2, s3, s4 = st.columns(4)

        with s1:

            st.metric(
                "Processed",
                stats["processed"]
            )

        with s2:

            st.metric(
                "Duplicates",
                stats["duplicates"]
            )

        with s3:

            st.metric(
                "Delayed",
                stats["delayed"]
            )

        with s4:

            st.metric(
                "Out of Order",
                stats["out_of_order"]
            )

        st.divider()

        state = processor.get_order_state(
            "ORD-1001"
        )

        st.subheader(
            "Final Order State"
        )

        if state:

            st.success(
                f"Final status: **{state['status']}**"
            )

            st.write(
                "The processor keeps the state associated with "
                "the latest valid event timestamp. This prevents "
                "older events from corrupting the current order state."
            )

        else:

            st.warning(
                "No order state found."
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "FoodPulse SLO Decision Center | "
    "Reliability Engineering Prototype | "
    "Human-in-the-loop governance | "
    "SQLite audit persistence"
)
