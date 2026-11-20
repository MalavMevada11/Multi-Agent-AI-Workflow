import os
import sys
from pathlib import Path

# Ensure project root is in sys.path so 'app' can always be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
from app.agents.coordinator import CoordinatorAgent
from app.schema.state import WorkflowState, WorkflowStep
from app.tools.db_generator import generate_synthetic_database
from app.config.settings import SQLITE_DB_PATH, SAMPLES_DIR

# Set page config
st.set_page_config(
    page_title="Multi-Agent AI Workflow for Automated BI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for presentation look
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e3a8a;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .ai-badge {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .thought-box {
        background-color: #f1f5f9;
        border-left: 4px solid #6366f1;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        font-family: monospace;
        font-size: 0.88rem;
        color: #1e293b;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .metric-badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .badge-compliant {
        background-color: #dcfce7;
        color: #166534;
    }
    .badge-violation {
        background-color: #fee2e2;
        color: #991b1b;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_coordinator():
    if not SQLITE_DB_PATH.exists():
        generate_synthetic_database(SQLITE_DB_PATH)
    return CoordinatorAgent()


coordinator = get_coordinator()

# -------------------------------------------------------------
# SIDEBAR CONTROLS & DEMO SCENARIOS
# -------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=64)
    st.title("AI Agent Control")
    st.markdown('<span class="ai-badge">GEMINI 2.5 FLASH POWERED</span>', unsafe_allow_html=True)
    st.caption("Autonomous Multi-Agent BI Orchestrator")

    st.divider()
    st.subheader("🎯 Presentation Demo Scenarios")
    preset_choice = st.selectbox(
        "Select Demo Scenario:",
        [
            "Custom Free-form Query",
            "1. HR: Malav Patel Leave Inquiry (Self-Service)",
            "2. Finance: Expense Policy Audit & Violations (BI)",
            "3. Finance: Budget Allocation vs Actual Spend (BI)",
            "4. Sales: Q3 Target & Commission Accelerator (BI)"
        ]
    )

    preset_queries = {
        "1. HR: Malav Patel Leave Inquiry (Self-Service)": "How many leaves are left for Malav Patel, and can he take 3 consecutive casual leaves under company policy?",
        "2. Finance: Expense Policy Audit & Violations (BI)": "Analyze all submitted expenses, check them against our reimbursement policy limits, and flag any violations.",
        "3. Finance: Budget Allocation vs Actual Spend (BI)": "Evaluate quarterly budget allocation versus actual expenditures across departments and identify overspends.",
        "4. Sales: Q3 Target & Commission Accelerator (BI)": "Analyze Q3 sales performance against targets and determine commission incentive accelerator eligibility."
    }

    selected_query = preset_queries.get(preset_choice, "")

    st.divider()
    st.subheader("⚙️ Overrides (Optional)")
    override_dept = st.selectbox("Department:", ["Auto-Detect", "HR", "Finance", "Sales"])
    override_mode = st.selectbox("Mode:", ["Auto-Detect", "Employee Self-Service", "Executive BI"])

    st.divider()
    with st.expander("🗄️ Inspect Enterprise Database"):
        try:
            import sqlite3
            conn = sqlite3.connect(str(SQLITE_DB_PATH))
            tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
            tbl = st.selectbox("View Table:", tables)
            preview_df = pd.read_sql_query(f"SELECT * FROM {tbl} LIMIT 5", conn)
            st.dataframe(preview_df, use_container_width=True)
            conn.close()
        except Exception as e:
            st.caption(f"DB Preview notice: {e}")


# -------------------------------------------------------------
# MAIN HEADER
# -------------------------------------------------------------
st.markdown('<div class="main-title">Multi-Agent AI Workflow for Automated Business Intelligence</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Multiple specialized Gemini AI Agents collaborate to dynamically query databases, cross-reference Pinecone vector policies, compute statistics, generate charts, and compile executive reports.</div>',
    unsafe_allow_html=True
)

query_input = st.text_input(
    "Enter your business intelligence or employee policy query:",
    value=selected_query or "How many leaves are left for Malav Patel, and can he take 3 consecutive casual leaves?",
    placeholder="e.g., Analyze Q3 expenses and flag policy violations..."
)

col_btn, col_info = st.columns([1, 5])
run_clicked = col_btn.button("🚀 Run Multi-Agent AI Workflow", type="primary")

if run_clicked or ("last_state" in st.session_state and not run_clicked):
    if run_clicked:
        dept_arg = None if override_dept == "Auto-Detect" else override_dept.lower()
        mode_arg = None if override_mode == "Auto-Detect" else ("employee_self_service" if "Employee" in override_mode else "executive_bi")

        step_events = []
        def on_step_update(step: WorkflowStep):
            step_events.append(step)

        with st.spinner("Gemini AI Agents communicating and executing workflow..."):
            state = coordinator.run_workflow(
                query=query_input,
                override_department=dept_arg,
                override_mode=mode_arg,
                step_callback=on_step_update
            )
            st.session_state["last_state"] = state
    else:
        state = st.session_state["last_state"]

    # -------------------------------------------------------------
    # ORCHESTRATION PLAN BANNER
    # -------------------------------------------------------------
    if state.plan:
        with st.container():
            st.markdown("### 📋 Dynamic AI Orchestration Plan")
            col1, col2, col3 = st.columns(3)
            col1.metric("Target Department", state.department.upper())
            col2.metric("Workflow Mode", state.mode.replace("_", " ").title())
            col3.metric("Entities Detected", ", ".join(state.plan.target_entities) if state.plan.target_entities else "General")
            if state.plan.reasoning:
                st.info(f"🧠 **Coordinator AI Reasoning:** {state.plan.reasoning}")

    # -------------------------------------------------------------
    # STEP-BY-STEP AGENT INSPECTOR (FOR PRESENTATION)
    # -------------------------------------------------------------
    st.subheader("🔍 Presentation View: Step-by-Step AI Agent Execution Inspector")
    st.caption("Live trace of specialized AI agents reasoning, querying databases, searching Pinecone policies, and creating visual deliverables.")

    steps = state.steps
    for idx, step in enumerate(steps, 1):
        with st.expander(f"**Step {idx}: [{step.agent_name}] {step.title}** ({step.status.upper()})", expanded=(idx in [1, 2, 3])):
            col_l, col_r = st.columns([3, 1])
            col_l.markdown(f"**Action Summary:** {step.summary}")
            col_r.caption(f"⏱️ Start: `{step.start_time}` | End: `{step.end_time}`")

            # Dedicated AI Thought Box
            if step.thought_process:
                st.markdown(f'<div class="thought-box">💭 <b>AI Cognitive Reasoning & Chain-of-Thought:</b><br/>{step.thought_process}</div>', unsafe_allow_html=True)

            # Context details
            details = step.details
            if "namespace" in details:
                st.markdown(f"**Pinecone Vector Namespace:** `{details.get('namespace')}` &nbsp;|&nbsp; **Retrieved:** `{details.get('retrieved_count')} governing clauses`")
                for p in details.get("policies", []):
                    st.info(f"📜 **{p.get('source')}** *(Similarity: {p.get('similarity_score')})*\n\n{p.get('snippet')}")

            if "sql_query" in details and details["sql_query"]:
                st.markdown("**AI Text-to-SQL Executed:**")
                st.code(details["sql_query"], language="sql")
                if details.get("preview_sample"):
                    st.markdown("**Sample Data Extracted:**")
                    st.dataframe(pd.DataFrame(details["preview_sample"]), use_container_width=True)

            if "compliance_status" in details:
                status = details["compliance_status"]
                badge_class = "badge-compliant" if status == "COMPLIANT" else "badge-violation"
                st.markdown(f'**Policy Compliance Audit Verdict:** <span class="metric-badge {badge_class}">{status}</span>', unsafe_allow_html=True)
                if details.get("policy_findings"):
                    st.markdown("**Policy Findings:**")
                    for finding in details["policy_findings"]:
                        st.write(f"- {finding}")
                if details.get("anomalies"):
                    st.markdown("**Detected Anomalies:**")
                    for anom in details["anomalies"]:
                        st.error(f"⚠️ {anom}")

            if "charts" in details:
                for c in details["charts"]:
                    st.success(f"📊 Synthesized Chart: **{c.get('title')}** ({c.get('type')})")

            if "pdf_path" in details and details["pdf_path"]:
                st.markdown(f"📄 **Executive PDF Artifact:** `{details['pdf_path']}`")

    st.divider()

    # -------------------------------------------------------------
    # DELIVERABLE TABS
    # -------------------------------------------------------------
    tab_report, tab_viz, tab_messages, tab_data, tab_export = st.tabs([
        "📑 Final Business Report",
        "📈 Visual Analytics",
        "💬 Inter-Agent Message Bus",
        "🗃️ Raw Data & Policy Context",
        "📥 PDF & Export"
    ])

    with tab_report:
        st.markdown(state.final_answer)

    with tab_viz:
        if state.charts:
            for chart in state.charts:
                st.subheader(chart.title)
                if Path(chart.file_path).exists():
                    st.image(chart.file_path, use_container_width=True)
                    st.caption(f"💡 **AI Narrative Takeaway:** {chart.key_takeaway}")
                else:
                    st.warning(f"Chart image not found at: {chart.file_path}")
        else:
            st.info("No visual charts required for this query.")

    with tab_messages:
        st.subheader("Inter-Agent Communication Bus")
        st.caption("Real-time message exchange between specialized AI agents during pipeline execution:")
        for msg in state.messages:
            with st.chat_message("user" if "Coordinator" in msg.sender else "assistant"):
                st.markdown(f"**From:** `{msg.sender}` ➔ **To:** `{msg.recipient}` *(at {msg.timestamp})*")
                st.write(msg.content)

    with tab_data:
        st.subheader("Structured Enterprise Records")
        if state.data_records:
            st.dataframe(pd.DataFrame(state.data_records), use_container_width=True)
        else:
            st.write("No raw records loaded.")

        st.subheader("Pinecone Policy Clauses")
        for p in state.policies:
            with st.chat_message("assistant", avatar="📜"):
                st.markdown(f"**Source:** {p.source} *(Similarity: {p.similarity_score:.4f})*")
                st.write(p.content)

    with tab_export:
        st.subheader("Download Executive Deliverable")
        if state.report and state.report.pdf_path and Path(state.report.pdf_path).exists():
            with open(state.report.pdf_path, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Download Executive PDF Report",
                data=pdf_bytes,
                file_name=Path(state.report.pdf_path).name,
                mime="application/pdf",
                type="primary"
            )
            st.success(f"PDF is compiled and ready for distribution: `{state.report.pdf_path}`")
        else:
            st.download_button(
                label="📥 Download Markdown Report",
                data=state.final_answer,
                file_name="BI_Report.md",
                mime="text/markdown"
            )
