import sys
from pathlib import Path

# Ensure project root is in sys.path so 'app' can always be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from app.agents.coordinator import CoordinatorAgent
from app.schema.state import WorkflowStep


def step_logger(step: WorkflowStep):
    """
    Prints clean, real-time step execution updates to the terminal.
    """
    status_icon = "⏳" if step.status == "running" else "✅" if step.status == "completed" else "❌"
    print(f"\n{status_icon} [{step.agent_name}] {step.title}")
    if step.summary:
        print(f"   ↳ {step.summary}")
    if step.status == "completed" and step.details:
        for k, v in step.details.items():
            if k in ["sql_query", "namespace", "compliance_status", "pdf_path"]:
                print(f"     • {k}: {v}")


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent AI Workflow for Automated Business Intelligence")
    parser.add_argument("--query", type=str, help="Business query or employee question to process")
    parser.add_argument("--dept", type=str, choices=["hr", "finance", "sales"], help="Optional department override")
    parser.add_argument("--mode", type=str, choices=["employee_self_service", "executive_bi"], help="Workflow mode")
    parser.add_argument("--emp", type=str, help="Employee name/ID override")
    args = parser.parse_args()

    print("=" * 75)
    print("🤖 MULTI-AGENT AI WORKFLOW FOR AUTOMATED BUSINESS INTELLIGENCE")
    print("   Data Sources → Retrieval → Analysis → Visualization → Insights → Report")
    print("=" * 75)

    coordinator = CoordinatorAgent()

    if args.query:
        print(f"\n[Incoming Query]: {args.query}")
        state = coordinator.run_workflow(
            query=args.query,
            override_department=args.dept,
            override_mode=args.mode,
            override_employee=args.emp,
            step_callback=step_logger
        )

        print("\n" + "=" * 75)
        print("📊 FINAL WORKFLOW OUTPUT")
        print("=" * 75)
        print(state.final_answer)

        if state.report and state.report.pdf_path:
            print(f"\n📄 PDF Report Compiled: {state.report.pdf_path}")
        return

    # Interactive Loop
    while True:
        query = input("\nEnter your business or policy query (type 'exit' to quit): ").strip()
        if not query:
            continue
        if query.lower() in ["exit", "quit", "q"]:
            print("\nShutting down multi-agent workflow. Goodbye!")
            break

        try:
            state = coordinator.run_workflow(
                query=query,
                step_callback=step_logger
            )

            print("\n" + "=" * 75)
            print("📊 FINAL WORKFLOW OUTPUT")
            print("=" * 75)
            print(state.final_answer)

            if state.report and state.report.pdf_path:
                print(f"\n📄 Downloadable PDF Report: {state.report.pdf_path}")

        except Exception as e:
            print(f"\n❌ Pipeline Execution Error: {e}")


if __name__ == "__main__":
    main()
