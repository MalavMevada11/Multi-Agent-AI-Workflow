import json
import logging
from typing import Callable, Optional
from app.agents.base_agent import BaseWorkflowAgent
from app.agents.retrieval_agent import DataAndPolicyRetrievalAgent
from app.agents.analysis_agent import DataAnalysisAndPolicyAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.report_agent import ReportGenerationAgent
from app.schema.state import WorkflowState, WorkflowStep, AgentPlan

logger = logging.getLogger(__name__)

COORDINATOR_SYSTEM_PROMPT = """
You are the Chief Coordinator Agent of an automated Multi-Agent Business Intelligence system.
Your mission is to understand user requests, identify the business domain, formulate an execution plan, and coordinate specialized downstream agents (Data Retrieval, Policy Verifier, Data Analyst, Visualizer, Report Generator).

Available Departments:
- HR: Employees, leave balances, vacation requests, attendance, HR workplace policies.
- Finance: Budgets, actual spend, expense claims, meal per-diems, travel flights, reimbursements, financial policies.
- Sales: Sales targets, deals, pipeline stages, commission rates, quotas, incentive plans.

Workflow Modes:
- employee_self_service: The user is an individual employee asking about their personal leave balance, eligibility, expense claim validity, or sales commission.
- executive_bi: The user is a business manager or executive asking for high-level BI, trends, audits, budget analysis, or automated departmental reports.

Instructions:
Analyze the user query and output a strict JSON object with this exact structure:
{
  "department": "hr" | "finance" | "sales",
  "mode": "employee_self_service" | "executive_bi",
  "target_entities": ["list of entities like employee names, quarters, numbers"],
  "sql_strategy": "Description of which tables and filters are required",
  "policy_topics": ["key policy topics to search in Pinecone"],
  "intent_summary": "1-sentence executive summary of the intent"
}
"""


class CoordinatorAgent(BaseWorkflowAgent):
    """
    AI Coordinator & Orchestration Engine.
    Uses Gemini to dynamically plan execution, decompose business problems,
    and sequence specialized agents with message tracing.
    """

    def __init__(self):
        super().__init__(agent_name="Coordinator Agent")
        self.retrieval_agent = DataAndPolicyRetrievalAgent()
        self.analysis_agent = DataAnalysisAndPolicyAgent()
        self.viz_agent = VisualizationAgent()
        self.report_agent = ReportGenerationAgent()

    def plan_workflow(self, query: str) -> tuple[str, AgentPlan]:
        """
        Uses Gemini to decompose query into an actionable AgentPlan.
        Falls back to rule-based classification if offline.
        """
        thought, response = self.brain.think_and_generate(
            system_prompt=COORDINATOR_SYSTEM_PROMPT,
            user_prompt=f"Analyze and create an orchestration plan for this query: '{query}'",
            expected_json=True
        )

        plan = None
        if response:
            try:
                data = json.loads(response)
                plan = AgentPlan(
                    intent_summary=data.get("intent_summary", "Automated BI Request"),
                    department=data.get("department", "hr").lower(),
                    mode=data.get("mode", "executive_bi"),
                    target_entities=data.get("target_entities", []),
                    sql_strategy=data.get("sql_strategy", "Query relevant department tables"),
                    policy_topics=data.get("policy_topics", []),
                    reasoning=thought
                )
            except Exception as e:
                logger.warning(f"Failed to parse LLM plan JSON: {e}")

        # Intelligent Fallback if LLM unavailable
        if not plan:
            q_lower = query.lower()
            dept = "hr"
            if any(w in q_lower for w in ["expense", "budget", "finance", "reimbursement", "dinner", "flight", "spend"]):
                dept = "finance"
            elif any(w in q_lower for w in ["sales", "target", "commission", "deal", "quota", "revenue"]):
                dept = "sales"

            is_self_service = any(w in q_lower for w in ["my", "for me", "how many", "can i", "patel", "malav"])
            mode = "employee_self_service" if is_self_service else "executive_bi"
            target_entities = ["Malav Patel"] if "malav" in q_lower or "patel" in q_lower else []

            thought = (
                f"Classified query into '{dept.upper()}' department based on business domain terms. "
                f"Mode set to '{mode}' due to query scope and personal intent."
            )
            plan = AgentPlan(
                intent_summary=f"Automated {dept.upper()} query processing",
                department=dept,
                mode=mode,
                target_entities=target_entities,
                sql_strategy=f"Extract records from {dept} tables",
                policy_topics=[f"{dept} policies"],
                reasoning=thought
            )

        return thought, plan

    def run_workflow(
        self,
        query: str,
        override_department: Optional[str] = None,
        override_mode: Optional[str] = None,
        override_employee: Optional[str] = None,
        step_callback: Optional[Callable[[WorkflowStep], None]] = None
    ) -> WorkflowState:
        """
        Orchestrates the entire multi-agent AI execution lifecycle.
        """
        # Step 1: AI Planning & Intent Decomposition
        thought, plan = self.plan_workflow(query)

        dept = override_department.lower() if override_department else plan.department
        mode = override_mode if override_mode else plan.mode
        emp_name = override_employee or (plan.target_entities[0] if plan.target_entities else None)

        state = WorkflowState(
            query=query,
            department=dept,
            mode=mode,
            employee_name=emp_name,
            plan=plan
        )

        routing_step = self.log_step_start(
            state=state,
            step_id="step_1_intent_routing",
            title="Coordinator AI: Dynamic Planning & Workflow Orchestration",
            summary=f"Synthesized execution plan for {dept.upper()} in '{mode.replace('_', ' ').title()}' mode.",
            thought_process=thought,
            callback=step_callback
        )

        # Message dispatch
        self.send_agent_message(
            state=state,
            recipient="DataAndPolicyRetrievalAgent",
            content=f"Execute dual retrieval: Query Pinecone for {dept} policies regarding {plan.policy_topics}; Execute SQL strategy: {plan.sql_strategy}."
        )

        self.log_step_complete(
            step=routing_step,
            summary=f"Plan formulated: {plan.intent_summary}",
            details={
                "department": dept,
                "mode": mode,
                "target_entities": plan.target_entities,
                "sql_strategy": plan.sql_strategy,
                "policy_topics": plan.policy_topics,
                "ai_thought": thought
            },
            thought_process=thought,
            callback=step_callback
        )

        # Step 2 & 3: Dual Retrieval Agent (AI Text-to-SQL + Pinecone)
        state = self.retrieval_agent.execute(state=state, step_callback=step_callback)

        # Step 4: Data Analysis & Policy Verification Agent (AI Reasoning)
        state = self.analysis_agent.execute(state=state, step_callback=step_callback)

        # Step 5: Visualization Agent (AI Chart Narrative)
        state = self.viz_agent.execute(state=state, step_callback=step_callback)

        # Step 6: Report Generation Agent (AI Executive Synthesis & PDF)
        state = self.report_agent.execute(state=state, step_callback=step_callback)

        return state
