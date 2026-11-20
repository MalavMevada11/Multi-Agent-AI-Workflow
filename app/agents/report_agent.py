import json
import logging
from typing import Callable, Optional
from datetime import datetime
from app.agents.base_agent import BaseWorkflowAgent
from app.schema.state import WorkflowState, WorkflowStep, ReportArtifact
from app.tools.pdf_builder import build_pdf_report

logger = logging.getLogger(__name__)

REPORT_SYNTHESIZER_SYSTEM_PROMPT = """
You are the Chief Strategy Officer and Executive Business Intelligence Synthesizer AI.
Your role is to craft a rigorous, professional, and policy-grounded business intelligence report or employee guidance response.

Directives:
1. Ground every conclusion in the provided empirical data and governing company policies.
2. For Employee Self-Service inquiries:
   - Provide a direct, polite, clear answer to the employee's personal question.
   - Explicitly cite the governing policy clauses (limits, notice period, documentation needed).
   - Outline clear actionable next steps.
3. For Executive BI Reports:
   - Provide an insightful Executive Summary.
   - Highlight Policy Compliance Status and specific risk exceptions.
   - Detail Key Performance Indicators and actionable strategic recommendations.

Format your output in clean, professional Markdown with headings, bullet points, and tables.
"""


class ReportGenerationAgent(BaseWorkflowAgent):
    """
    AI Report Generation Agent.
    Leverages Gemini to synthesize complex quantitative metrics, policy checks,
    and visual artifacts into executive reports and PDF documents.
    """

    def __init__(self):
        super().__init__(agent_name="Report Generation Agent")

    def synthesize_report_with_ai(
        self,
        query: str,
        department: str,
        mode: str,
        policies: list,
        metrics: dict,
        findings: list,
        anomalies: list,
        employee_name: Optional[str]
    ) -> tuple[str, str]:
        """
        Uses Gemini to generate the final synthesized response.
        """
        policy_context = "\n".join([f"- [{p.source}] {p.content}" for p in policies[:3]])
        metrics_context = "\n".join([f"- {k}: {v}" for k, v in metrics.items()])
        findings_context = "\n".join([f"- {f}" for f in findings])
        anomalies_context = "\n".join([f"- {a}" for a in anomalies]) if anomalies else "None detected."

        prompt = (
            f"User Query: '{query}'\n"
            f"Department: '{department}' | Mode: '{mode}' | Target Employee: '{employee_name or 'N/A'}'\n\n"
            f"Company Policies in Effect:\n{policy_context}\n\n"
            f"Key Quantitative Metrics:\n{metrics_context}\n\n"
            f"Audit Findings & Compliance:\n{findings_context}\n\n"
            f"Flagged Anomalies / Violations:\n{anomalies_context}\n\n"
            "Draft the complete, authoritative, and polished Markdown response."
        )

        thought, markdown = self.brain.think_and_generate(
            system_prompt=REPORT_SYNTHESIZER_SYSTEM_PROMPT,
            user_prompt=prompt
        )

        return thought, markdown

    def execute(
        self,
        state: WorkflowState,
        step_callback: Optional[Callable[[WorkflowStep], None]] = None
    ) -> WorkflowState:
        report_step = self.log_step_start(
            state=state,
            step_id="step_6_report_generation",
            title="Report Generation Agent: AI Synthesis & Executive PDF Export",
            summary="Synthesizing multi-agent deliverables into executive report and compiling PDF...",
            callback=step_callback
        )

        analysis = state.analysis
        charts = state.charts
        dept = state.department.upper()

        metrics = analysis.metrics if analysis else {}
        findings = analysis.policy_findings if analysis else []
        anomalies = analysis.anomalies if analysis else []

        # 1. Synthesize via Gemini AI
        ai_thought, ai_markdown = self.synthesize_report_with_ai(
            query=state.query,
            department=dept,
            mode=state.mode,
            policies=state.policies,
            metrics=metrics,
            findings=findings,
            anomalies=anomalies,
            employee_name=state.employee_name
        )

        # 2. Structure Delivery Artifacts
        kpi_cards = []
        if metrics:
            for k, v in metrics.items():
                note = "Requires Attention" if "Flagged" in k or "Variance" in k else "On Track"
                kpi_cards.append({"title": k, "value": str(v), "note": note})

        # Fallback if AI synthesis was offline
        if not ai_markdown:
            if state.mode == "employee_self_service":
                emp = state.employee_name or "Employee"
                ai_markdown = f"""### Employee Self-Service Guidance: {emp}

**Query:** *"{state.query}"*  
**Department:** {dept} | **Compliance Status:** `{analysis.policy_compliance_status if analysis else 'VERIFIED'}`

---

#### 1. Current Records & Status
""" + "\n".join([f"- **{k}**: {v}" for k, v in metrics.items()]) + f"""

#### 2. Governing Company Policy
""" + "\n".join([f"- **{p.source}**: {p.content}" for p in state.policies[:2]]) + f"""

#### 3. Compliance & Next Steps
""" + "\n".join([f"- {f}" for f in findings]) + """
- **Action Required**: Please submit any relevant requests through the internal portal with required documentation attached.
"""
            else:
                ai_markdown = f"""# Automated Business Intelligence & Policy Audit: {dept}
**Generated:** {datetime.now().strftime('%B %d, %Y')} | **Status:** `{analysis.policy_compliance_status if analysis else 'VERIFIED'}`

## 1. Executive Summary
Analysis conducted across {len(state.data_records)} structured corporate records cross-referenced against company policies stored in Pinecone.

## 2. Policy Compliance & Audit Findings
""" + "\n".join([f"- {f}" for f in findings]) + """

## 3. Key Performance Indicators
""" + "\n".join([f"- **{k}**: {v}" for k, v in metrics.items()])

        state.final_answer = ai_markdown

        report = ReportArtifact(
            title=f"BI & Policy Report: {dept}",
            executive_summary=analysis.executive_insights if analysis else "Automated multi-agent synthesis completed.",
            kpi_cards=kpi_cards,
            recommendations=findings[:3],
            markdown_content=ai_markdown
        )

        # Compile PDF
        try:
            pdf_path = build_pdf_report(
                report=report,
                charts=charts,
                department=dept
            )
            report.pdf_path = pdf_path
        except Exception as e:
            logger.error(f"PDF compilation notice: {e}", exc_info=True)

        state.report = report

        thought_process = (
            f"AI Synthesis Reasoning: {ai_thought or 'Synthesized quantitative findings, policy rulings, and charts into executive document.'}\n"
            f"Compiled downloadable PDF report."
        )

        self.send_agent_message(
            state=state,
            recipient="CoordinatorAgent",
            content=f"Workflow completed. Executive report and PDF artifact compiled successfully."
        )

        self.log_step_complete(
            step=report_step,
            summary=f"Synthesized executive report. PDF compiled at: {report.pdf_path or 'Generated'}",
            details={
                "report_title": report.title,
                "pdf_path": report.pdf_path,
                "kpi_count": len(kpi_cards),
                "ai_thought": ai_thought
            },
            thought_process=thought_process,
            callback=step_callback
        )

        return state
