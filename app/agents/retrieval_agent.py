import logging
import re
from typing import Callable, Optional
import pandas as pd
from app.agents.base_agent import BaseWorkflowAgent
from app.retrieval.pinecone_retriever import PolicyRetriever
from app.retrieval.sql_retriever import StructuredDataRetriever
from app.schema.state import WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)

SQL_GENERATOR_SYSTEM_PROMPT = """
You are an expert Enterprise Data Engineer AI.
Your mission is to generate a clean, safe, valid SQLite SELECT query based on the user's question and the database schema.

Database Schema:
1. employees (employee_id TEXT, name TEXT, department TEXT, role TEXT, email TEXT, joining_date TEXT, salary REAL, manager_name TEXT)
2. leave_balances (balance_id INTEGER, employee_id TEXT, leave_type TEXT, total_entitled INTEGER, used_days INTEGER, remaining_days INTEGER, fiscal_year INTEGER)
3. leave_requests (request_id TEXT, employee_id TEXT, leave_type TEXT, days_requested INTEGER, start_date TEXT, end_date TEXT, status TEXT, reason TEXT)
4. department_budgets (budget_id INTEGER, department TEXT, quarter TEXT, allocated_budget REAL, actual_spend REAL, variance REAL, fiscal_year INTEGER)
5. expenses (expense_id TEXT, employee_id TEXT, department TEXT, category TEXT, amount REAL, expense_date TEXT, description TEXT, status TEXT, pre_approved INTEGER)
6. sales_targets (target_id INTEGER, employee_id TEXT, quarter TEXT, target_amount REAL, achieved_amount REAL, achievement_rate REAL, quota_met INTEGER)
7. deals (deal_id TEXT, employee_id TEXT, client_name TEXT, deal_value REAL, stage TEXT, close_date TEXT, region TEXT)
8. commissions (commission_id TEXT, employee_id TEXT, deal_id TEXT, deal_value REAL, commission_rate REAL, commission_earned REAL, status TEXT)

RULES:
- ONLY output a valid SQLite SELECT query. Do NOT use INSERT, UPDATE, DROP, or DELETE.
- Use JOINs when necessary (e.g. join employees on employee_id).
- For employee names, use case-insensitive partial match: LOWER(name) LIKE '%...%'.
- IMPORTANT: When querying leave balances, always SELECT all leave_balances columns (e.g. lb.leave_type, lb.total_entitled, lb.used_days, lb.remaining_days) alongside employee details.
- When querying expenses, always SELECT category, amount, description, status, pre_approved.
- When querying budgets, always SELECT department, quarter, allocated_budget, actual_spend, variance.
- When querying sales, always SELECT target_amount, achieved_amount, achievement_rate, quota_met.
- Do not output markdown code blocks or explanations in the final output; just the raw SQL query.
"""


class DataAndPolicyRetrievalAgent(BaseWorkflowAgent):
    """
    AI Data & Policy Retrieval Agent.
    Combines Gemini-driven dynamic Text-to-SQL generation with Pinecone semantic policy retrieval.
    """

    def __init__(self):
        super().__init__(agent_name="Data & Policy Retrieval Agent")
        self.policy_retriever = PolicyRetriever()
        self.sql_retriever = StructuredDataRetriever()

    def generate_dynamic_sql(self, query: str, department: str, employee_name: Optional[str]) -> tuple[str, str]:
        """
        Uses Gemini to dynamically write a targeted SQL query based on the schema and intent.
        """
        prompt = (
            f"User Question: '{query}'\n"
            f"Target Department: '{department}'\n"
            f"Identified Employee: '{employee_name or 'N/A'}'\n"
            "Generate the optimal SQLite SELECT query to answer this question."
        )

        thought, sql = self.brain.think_and_generate(
            system_prompt=SQL_GENERATOR_SYSTEM_PROMPT,
            user_prompt=prompt
        )

        # Clean SQL string
        sql = sql.strip().replace("```sql", "").replace("```", "").strip()

        # Sanity check: must be a SELECT statement
        if not sql.upper().startswith("SELECT"):
            sql = ""

        return thought, sql

    def execute(
        self,
        state: WorkflowState,
        step_callback: Optional[Callable[[WorkflowStep], None]] = None
    ) -> WorkflowState:
        dept = state.department.lower()
        namespace = f"{dept}-policies" if dept in ["hr", "finance", "sales"] else "hr-policies"

        # -------------------------------------------------------------
        # STEP 2: PINECONE POLICY RETRIEVAL
        # -------------------------------------------------------------
        policy_step = self.log_step_start(
            state=state,
            step_id="step_2_policy_retrieval",
            title=f"Policy Retrieval Agent: Pinecone Vector Search ({namespace})",
            summary=f"Searching Pinecone index for verified {dept.upper()} company policies...",
            callback=step_callback
        )

        policies = self.policy_retriever.retrieve_policies(namespace=namespace, query=state.query)
        state.policies = policies

        policy_thought = (
            f"Queried Pinecone namespace '{namespace}' using semantic similarity. "
            f"Found {len(policies)} governing policy clauses regarding entitlements, limits, and approval protocols."
        )

        self.log_step_complete(
            step=policy_step,
            summary=f"Retrieved {len(policies)} governing policy clause(s) from Pinecone namespace '{namespace}'.",
            details={
                "namespace": namespace,
                "retrieved_count": len(policies),
                "policies": [
                    {
                        "source": p.source,
                        "similarity_score": round(p.similarity_score, 4),
                        "snippet": p.content[:200] + "..." if len(p.content) > 200 else p.content
                    }
                    for p in policies
                ]
            },
            thought_process=policy_thought,
            callback=step_callback
        )

        # -------------------------------------------------------------
        # STEP 3: STRUCTURED DATA RETRIEVAL (DYNAMIC TEXT-TO-SQL)
        # -------------------------------------------------------------
        data_step = self.log_step_start(
            state=state,
            step_id="step_3_data_retrieval",
            title="Data Retrieval Agent: Dynamic Text-to-SQL & Database Query",
            summary="Analyzing database schema and formulating targeted SQL queries...",
            callback=step_callback
        )

        # Generate SQL using Gemini
        sql_thought, dynamic_sql = self.generate_dynamic_sql(
            query=state.query,
            department=dept,
            employee_name=state.employee_name
        )

        sql_executed = dynamic_sql
        records = []
        df = pd.DataFrame()

        # Try executing dynamically generated SQL
        if sql_executed:
            try:
                records, df = self.sql_retriever.execute_query(sql_executed)
            except Exception as e:
                logger.warning(f"Dynamic SQL failed: {e}. Falling back to domain catalog query.")
                sql_executed = ""

        # Fallback to domain catalog query if needed
        if not sql_executed or df.empty:
            if state.mode == "employee_self_service" and state.employee_name:
                target_emp = state.employee_name
                if dept == "hr" or "leave" in state.query.lower():
                    sql_executed, records, df = self.sql_retriever.query_employee_leaves(target_emp)
                elif dept == "finance":
                    sql_executed, records, df = self.sql_retriever.query_department_expenses(department=None)
                    if not df.empty and "employee_name" in df.columns:
                        df = df[df["employee_name"].str.lower().str.contains(target_emp.lower())]
                        records = df.to_dict(orient="records")
                elif dept == "sales":
                    sql_executed, records, df = self.sql_retriever.query_sales_performance()
            else:
                if dept == "hr":
                    sql_executed = """
                    SELECT e.employee_id, e.name, e.department, lb.leave_type, lb.total_entitled, lb.used_days, lb.remaining_days
                    FROM employees e
                    JOIN leave_balances lb ON e.employee_id = lb.employee_id
                    """
                    records, df = self.sql_retriever.execute_query(sql_executed)
                elif dept == "finance":
                    if "budget" in state.query.lower() or "spend" in state.query.lower():
                        sql_executed, records, df = self.sql_retriever.query_department_budgets()
                    else:
                        sql_executed, records, df = self.sql_retriever.query_department_expenses()
                elif dept == "sales":
                    sql_executed, records, df = self.sql_retriever.query_sales_performance()

        state.data_records = records
        state.raw_data_summary = {
            "row_count": len(records),
            "columns": list(df.columns) if not df.empty else [],
            "sql_query": sql_executed
        }

        combined_data_thought = (
            f"AI Reasoning: {sql_thought or 'Synthesized schema query strategy.'} "
            f"Successfully executed SQL query and extracted {len(records)} verified records from SQLite database."
        )

        self.send_agent_message(
            state=state,
            recipient="DataAnalysisAndPolicyAgent",
            content=f"Extracted {len(records)} records from SQLite database using SQL: {sql_executed.strip()}. Forwarding to Analysis Agent."
        )

        self.log_step_complete(
            step=data_step,
            summary=f"Extracted {len(records)} records via Text-to-SQL engine.",
            details={
                "sql_query": sql_executed.strip() if sql_executed else "Catalog Query",
                "row_count": len(records),
                "columns": list(df.columns) if not df.empty else [],
                "preview_sample": records[:3] if records else []
            },
            thought_process=combined_data_thought,
            callback=step_callback
        )

        return state
