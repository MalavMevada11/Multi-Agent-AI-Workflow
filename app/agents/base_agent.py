import logging
from typing import Callable, Optional
from app.agents.llm_service import GeminiAgentBrain
from app.config.settings import GEMINI_MODEL_NAME
from app.schema.state import WorkflowState, WorkflowStep

logger = logging.getLogger(__name__)


class BaseWorkflowAgent:
    """
    Base AI Agent class in the Multi-Agent BI Architecture.
    Equipped with a Gemini LLM brain, step telemetry, and message exchange capabilities.
    """

    def __init__(self, agent_name: str, model_name: str = GEMINI_MODEL_NAME):
        self.agent_name = agent_name
        self.model_name = model_name
        self.brain = GeminiAgentBrain(model_name=model_name)

    def log_step_start(
        self,
        state: WorkflowState,
        step_id: str,
        title: str,
        summary: str = "",
        thought_process: str = "",
        callback: Optional[Callable[[WorkflowStep], None]] = None
    ) -> WorkflowStep:
        step = state.get_or_create_step(step_id, self.agent_name, title)
        step.start(summary=summary, thought_process=thought_process)
        if callback:
            callback(step)
        return step

    def log_step_complete(
        self,
        step: WorkflowStep,
        summary: str = "",
        details: Optional[dict] = None,
        thought_process: str = "",
        callback: Optional[Callable[[WorkflowStep], None]] = None
    ):
        step.complete(summary=summary, details=details, thought_process=thought_process)
        if callback:
            callback(step)

    def log_step_fail(
        self,
        step: WorkflowStep,
        error_msg: str,
        callback: Optional[Callable[[WorkflowStep], None]] = None
    ):
        step.fail(error_msg)
        if callback:
            callback(step)

    def send_agent_message(self, state: WorkflowState, recipient: str, content: str):
        """Broadcasts an agent-to-agent message onto the shared state message bus."""
        state.add_message(sender=self.agent_name, recipient=recipient, content=content)
