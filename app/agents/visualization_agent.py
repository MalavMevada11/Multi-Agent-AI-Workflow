import logging
from typing import Callable, Optional
import pandas as pd
from app.agents.base_agent import BaseWorkflowAgent
from app.schema.state import WorkflowState, WorkflowStep
from app.tools.chart_tools import (
    render_leave_balance_chart,
    render_budget_vs_spend_chart,
    render_expenses_compliance_chart,
    render_sales_performance_chart
)

logger = logging.getLogger(__name__)

VIZ_NARRATIVE_SYSTEM_PROMPT = """
You are an expert Data Storyteller and AI Visual Analytics Architect.
Given a business intelligence chart type, title, and statistical context, generate a 1-sentence punchy, executive takeaway that directly translates the visualization into business meaning.
Do not describe the chart axis; explain what the business finding implies.
"""


class VisualizationAgent(BaseWorkflowAgent):
    """
    AI Visualization Agent.
    Selects optimal charting narratives, executes Matplotlib/Seaborn rendering,
    and synthesizes executive storytelling takeaways using Gemini.
    """

    def __init__(self):
        super().__init__(agent_name="Visualization Agent")

    def synthesize_chart_narrative(self, title: str, chart_type: str, stats_context: str) -> str:
        """
        Uses Gemini to generate an executive takeaway caption for the chart.
        """
        prompt = f"Chart: '{title}' ({chart_type})\nContext: {stats_context}\nGenerate executive takeaway:"
        _, takeaway = self.brain.think_and_generate(
            system_prompt=VIZ_NARRATIVE_SYSTEM_PROMPT,
            user_prompt=prompt
        )
        return takeaway.strip().replace('"', '') if takeaway else "Key metrics charted against governance targets."

    def execute(
        self,
        state: WorkflowState,
        step_callback: Optional[Callable[[WorkflowStep], None]] = None
    ) -> WorkflowState:
        viz_step = self.log_step_start(
            state=state,
            step_id="step_5_visualization",
            title="Visualization Agent: Automated Visual Analytics & Chart Generation",
            summary="Analyzing metrics distribution and rendering tailored Matplotlib/Seaborn figures...",
            callback=step_callback
        )

        df = pd.DataFrame(state.data_records)
        charts = []
        viz_thought = ""

        if not df.empty:
            dept = state.department.lower()

            try:
                # Domain 1: HR
                if (dept == "hr" or "leave" in state.query.lower()) and "leave_type" in df.columns:
                    emp_name = state.employee_name or (df.iloc[0]["name"] if "name" in df.columns else "Employee")
                    viz_thought = f"Selected Horizontal Bar Chart to visualize leave entitlement vs consumption for {emp_name}."
                    chart = render_leave_balance_chart(df, employee_name=emp_name)
                    # Enhance with AI narrative if available
                    ai_takeaway = self.synthesize_chart_narrative(chart.title, chart.chart_type, f"Leave usage for {emp_name}")
                    if ai_takeaway:
                        chart.key_takeaway = ai_takeaway
                    charts.append(chart)

                # Domain 2: Finance
                elif dept == "finance" or "expense" in state.query.lower() or "budget" in state.query.lower():
                    if "allocated_budget" in df.columns:
                        viz_thought = "Selected Grouped Bar Chart to contrast budget allocation vs actual expenditure burn rates."
                        chart = render_budget_vs_spend_chart(df, department="Enterprise Budgets")
                        charts.append(chart)
                    if "category" in df.columns and "amount" in df.columns:
                        viz_thought += " Selected Stacked Bar Chart to isolate policy-flagged expense categories."
                        chart = render_expenses_compliance_chart(df)
                        charts.append(chart)

                # Domain 3: Sales
                elif dept == "sales" and "achieved_amount" in df.columns:
                    viz_thought = "Selected Dual Column Chart to evaluate quota attainment percentages against Q3 targets."
                    chart = render_sales_performance_chart(df, quarter="Q3")
                    charts.append(chart)

            except Exception as e:
                logger.error(f"Error during AI visualization generation: {e}", exc_info=True)

        state.charts = charts

        self.send_agent_message(
            state=state,
            recipient="ReportGenerationAgent",
            content=f"Generated {len(charts)} visual charts. Transmitting image artifacts to Report Generator."
        )

        self.log_step_complete(
            step=viz_step,
            summary=f"Synthesized {len(charts)} publication-ready visualization artifact(s).",
            details={
                "generated_charts_count": len(charts),
                "charts": [
                    {
                        "title": c.title,
                        "type": c.chart_type,
                        "path": c.file_path,
                        "takeaway": c.key_takeaway
                    }
                    for c in charts
                ]
            },
            thought_process=viz_thought,
            callback=step_callback
        )

        return state
