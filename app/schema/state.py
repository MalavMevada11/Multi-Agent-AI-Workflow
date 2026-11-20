from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentMessage(BaseModel):
    sender: str
    recipient: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


class AgentPlan(BaseModel):
    intent_summary: str = ""
    department: str = "general"
    mode: Literal["employee_self_service", "executive_bi"] = "executive_bi"
    target_entities: List[str] = Field(default_factory=list)
    sql_strategy: str = ""
    policy_topics: List[str] = Field(default_factory=list)
    reasoning: str = ""


class WorkflowStep(BaseModel):
    step_id: str
    agent_name: str
    title: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    summary: str = ""
    thought_process: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)

    def start(self, summary: str = "", thought_process: str = ""):
        self.status = StepStatus.RUNNING
        self.start_time = datetime.now().strftime("%H:%M:%S")
        if summary:
            self.summary = summary
        if thought_process:
            self.thought_process = thought_process

    def complete(self, summary: str = "", details: Optional[Dict[str, Any]] = None, thought_process: str = ""):
        self.status = StepStatus.COMPLETED
        self.end_time = datetime.now().strftime("%H:%M:%S")
        if summary:
            self.summary = summary
        if thought_process:
            self.thought_process = thought_process
        if details:
            self.details.update(details)

    def fail(self, error_message: str):
        self.status = StepStatus.FAILED
        self.end_time = datetime.now().strftime("%H:%M:%S")
        self.summary = f"Failed: {error_message}"
        self.details["error"] = error_message


class PolicyReference(BaseModel):
    namespace: str
    source: str
    content: str
    similarity_score: float = 0.0


class ChartArtifact(BaseModel):
    chart_id: str
    title: str
    chart_type: str
    file_path: str
    key_takeaway: str


class AnalysisArtifact(BaseModel):
    summary: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    trends: List[str] = Field(default_factory=list)
    anomalies: List[str] = Field(default_factory=list)
    policy_compliance_status: Literal[
        "COMPLIANT",
        "FLAGGED_VIOLATIONS",
        "REQUIRES_APPROVAL",
        "NOT_APPLICABLE"
    ] = "NOT_APPLICABLE"
    policy_findings: List[str] = Field(default_factory=list)
    executive_insights: str = ""


class ReportArtifact(BaseModel):
    title: str
    executive_summary: str
    kpi_cards: List[Dict[str, str]] = Field(default_factory=list)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    markdown_content: str = ""
    pdf_path: Optional[str] = None


class WorkflowState(BaseModel):
    query: str
    department: str = "general"
    mode: Literal["employee_self_service", "executive_bi"] = "executive_bi"
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None

    plan: Optional[AgentPlan] = None
    messages: List[AgentMessage] = Field(default_factory=list)
    steps: List[WorkflowStep] = Field(default_factory=list)
    policies: List[PolicyReference] = Field(default_factory=list)
    raw_data_summary: Dict[str, Any] = Field(default_factory=dict)
    data_records: List[Dict[str, Any]] = Field(default_factory=list)

    analysis: Optional[AnalysisArtifact] = None
    charts: List[ChartArtifact] = Field(default_factory=list)
    report: Optional[ReportArtifact] = None
    final_answer: str = ""

    def add_message(self, sender: str, recipient: str, content: str):
        self.messages.append(AgentMessage(sender=sender, recipient=recipient, content=content))

    def get_or_create_step(self, step_id: str, agent_name: str, title: str) -> WorkflowStep:
        for step in self.steps:
            if step.step_id == step_id:
                return step
        step = WorkflowStep(step_id=step_id, agent_name=agent_name, title=title)
        self.steps.append(step)
        return step
