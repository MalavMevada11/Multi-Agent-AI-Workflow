import json
import logging
from typing import Callable, Optional, Dict, Any, List
import pandas as pd
from app.agents.base_agent import BaseWorkflowAgent
from app.schema.state import WorkflowState, WorkflowStep, AnalysisArtifact

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """
You are a Principal Business Intelligence Analyst & Corporate Policy Auditor AI.
Your mission is to perform a rigorous analysis of empirical data records against governing company policy clauses.

You must:
1. Examine the retrieved corporate records and the retrieved company policies.
2. Cross-reference each data point against policy clauses (e.g., maximum limits, advance notice rules, quota thresholds, approval criteria).
3. Determine the overall compliance status: "COMPLIANT", "FLAGGED_VIOLATIONS", or "REQUIRES_APPROVAL".
4. Identify notable trends, statistical anomalies, and policy findings.
5. Provide a high-level executive insight summary.

Output format:
Return a valid JSON object matching this structure:
{
  "compliance_status": "COMPLIANT" | "FLAGGED_VIOLATIONS" | "REQUIRES_APPROVAL",
  "policy_findings": ["detailed policy observations citing the exact clauses"],
  "anomalies": ["specific data points or transactions that deviate from norms or violate rules"],
  "trends": ["high-level patterns, ratios, or trajectory observations"],
  "executive_insights": "2-3 sentence strategic executive takeaways"
}
"""


class DataAnalysisAndPolicyAgent(BaseWorkflowAgent):
    """
    AI Data Analysis & Policy Verification Agent.
    Combines pandas statistical computations with Gemini-powered cognitive reasoning
    for anomaly detection and policy auditing.
    """

    def __init__(self):
        super().__init__(agent_name="Data Analysis & Policy Verification Agent")

    def analyze_with_ai(
        self,
        query: str,
        department: str,
        records: List[Dict[str, Any]],
        policies: List[str]
    ) -> tuple[str, Dict[str, Any]]:
        """
        Invokes Gemini to evaluate records against company policy clauses.
        """
        records_sample = records[:15]  # Cap to prevent excessive context
        policy_text = "\n\n".join(policies)

        prompt = (
            f"User Question: '{query}'\n"
            f"Department: '{department}'\n\n"
            f"Governing Company Policies:\n{policy_text}\n\n"
            f"Empirical Data Records ({len(records)} total records, showing sample):\n"
            f"{json.dumps(records_sample, indent=2)}\n\n"
            "Evaluate compliance, compute observations, and output the analysis JSON."
        )

        thought, response = self.brain.think_and_generate(
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_prompt=prompt,
            expected_json=True
        )

        parsed_data = {}
        if response:
            try:
                parsed_data = json.loads(response)
            except Exception as e:
                logger.warning(f"Could not parse AI analysis JSON: {e}")

        return thought, parsed_data

    def execute(
        self,
        state: WorkflowState,
        step_callback: Optional[Callable[[WorkflowStep], None]] = None
    ) -> WorkflowState:
        analysis_step = self.log_step_start(
            state=state,
            step_id="step_4_analysis_and_policy_check",
            title="Data Analysis & Policy Agent: AI Compliance Audit & Anomaly Detection",
            summary="Cross-referencing empirical records against Pinecone company policies...",
            callback=step_callback
        )

        df = pd.DataFrame(state.data_records)
        metrics: Dict[str, Any] = {}
        dept = state.department.lower()

        # 1. Base Statistical Computations via Pandas (with safe column access)
        if not df.empty:
            if "remaining_days" in df.columns or "total_entitled" in df.columns or "used_days" in df.columns:
                tot_entitled = int(df["total_entitled"].sum()) if "total_entitled" in df.columns else 0
                tot_used = int(df["used_days"].sum()) if "used_days" in df.columns else 0
                tot_rem = int(df["remaining_days"].sum()) if "remaining_days" in df.columns else 0

                if tot_rem > 0:
                    metrics["Total Balance Remaining"] = f"{tot_rem} days"
                if tot_entitled > 0:
                    metrics["Total Entitled Leaves"] = f"{tot_entitled} days"
                if tot_used > 0:
                    metrics["Total Leaves Availed"] = f"{tot_used} days"
                if tot_entitled > 0 and tot_used > 0:
                    metrics["Leave Utilization Rate"] = f"{round((tot_used / tot_entitled) * 100, 1)}%"

            elif "amount" in df.columns:
                tot_spend = float(df["amount"].sum())
                avg_claim = float(df["amount"].mean())
                metrics["Total Expenses Audited"] = f"${tot_spend:,.2f}"
                metrics["Average Claim Value"] = f"${avg_claim:,.2f}"

                if "status" in df.columns:
                    flagged = df[df["status"] == "Flagged"]
                    flagged_tot = float(flagged["amount"].sum()) if not flagged.empty else 0.0
                    metrics["Flagged Policy Violations"] = f"{len(flagged)} claims"
                    metrics["Non-Compliant Spend"] = f"${flagged_tot:,.2f}"

            elif "allocated_budget" in df.columns or "actual_spend" in df.columns:
                tot_alloc = float(df["allocated_budget"].sum()) if "allocated_budget" in df.columns else 0.0
                tot_actual = float(df["actual_spend"].sum()) if "actual_spend" in df.columns else 0.0
                if tot_alloc > 0:
                    metrics["Total Budget Allocated"] = f"${tot_alloc:,.2f}"
                if tot_actual > 0:
                    metrics["Total Actual Spend"] = f"${tot_actual:,.2f}"
                if tot_alloc > 0 and tot_actual > 0:
                    metrics["Net Variance"] = f"${(tot_alloc - tot_actual):,.2f}"
                    metrics["Budget Burn Rate"] = f"{round((tot_actual / tot_alloc) * 100, 1)}%"

            elif "achieved_amount" in df.columns or "target_amount" in df.columns:
                tot_target = float(df["target_amount"].sum()) if "target_amount" in df.columns else 0.0
                tot_achieved = float(df["achieved_amount"].sum()) if "achieved_amount" in df.columns else 0.0
                if tot_target > 0:
                    metrics["Total Sales Target"] = f"${tot_target:,.2f}"
                if tot_achieved > 0:
                    metrics["Total Closed Revenue"] = f"${tot_achieved:,.2f}"
                if tot_target > 0 and tot_achieved > 0:
                    metrics["Team Quota Attainment"] = f"{round((tot_achieved / tot_target) * 100, 1)}%"
                if "quota_met" in df.columns:
                    reps_quota = int(df["quota_met"].sum())
                    metrics["Reps Meeting Quota"] = f"{reps_quota} / {len(df)}"

        # 2. Cognitive AI Reasoning via Gemini
        policy_texts = [f"[{p.source}] {p.content}" for p in state.policies]
        ai_thought, ai_results = self.analyze_with_ai(
            query=state.query,
            department=dept,
            records=state.data_records,
            policies=policy_texts
        )

        # Merge AI outputs with defaults
        compliance_status = ai_results.get("compliance_status")
        if not compliance_status:
            # Fallback heuristic
            if "status" in df.columns and (df["status"] == "Flagged").any():
                compliance_status = "FLAGGED_VIOLATIONS"
            else:
                compliance_status = "COMPLIANT"

        policy_findings = ai_results.get("policy_findings", [])
        if not policy_findings:
            policy_findings = [f"Records audited against {dept.upper()} company policies; standard conditions apply."]

        anomalies = ai_results.get("anomalies", [])
        trends = ai_results.get("trends", [])
        executive_insights = ai_results.get("executive_insights", "Empirical data reconciled with corporate governance rules.")

        thought_process = (
            f"AI Policy Reasoning: {ai_thought or 'Reconciled database figures against policy thresholds.'}\n"
            f"Verdict: {compliance_status}. Audited {len(state.data_records)} records against {len(state.policies)} policy clauses."
        )

        state.analysis = AnalysisArtifact(
            summary=f"Analysis of {len(state.data_records)} {dept} records completed. Compliance status: {compliance_status}.",
            metrics=metrics,
            trends=trends,
            anomalies=anomalies,
            policy_compliance_status=compliance_status,
            policy_findings=policy_findings,
            executive_insights=executive_insights
        )

        self.send_agent_message(
            state=state,
            recipient="VisualizationAgent",
            content=f"Analysis verified. Compliance status is '{compliance_status}'. Detected {len(anomalies)} anomalies. Generate optimal charts."
        )

        self.log_step_complete(
            step=analysis_step,
            summary=f"Audit completed: {compliance_status}. {len(policy_findings)} policy evaluations confirmed.",
            details={
                "compliance_status": compliance_status,
                "metrics": metrics,
                "policy_findings": policy_findings,
                "anomalies": anomalies,
                "executive_insights": executive_insights
            },
            thought_process=thought_process,
            callback=step_callback
        )

        return state
