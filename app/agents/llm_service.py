import os
import json
import re
import logging
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.config.settings import GEMINI_MODEL_NAME, GOOGLE_API_KEY

logger = logging.getLogger(__name__)


class GeminiAgentBrain:
    """
    Dedicated LLM integration service for AI agents in the Multi-Agent BI system.
    Leverages Google Gemini (gemini-2.5-flash) for reasoning, dynamic Text-to-SQL,
    statistical interpretation, and executive synthesis with graceful resilience.
    """

    def __init__(self, model_name: str = GEMINI_MODEL_NAME):
        self.model_name = model_name
        self._llm = None
        self._init_llm()

    def _init_llm(self):
        try:
            api_key = GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
            if api_key:
                self._llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=api_key,
                    temperature=0.2,
                    timeout=30
                )
        except Exception as e:
            logger.warning(f"Gemini LLM initialization notice: {e}")
            self._llm = None

    def is_available(self) -> bool:
        return self._llm is not None

    def think_and_generate(
        self,
        system_prompt: str,
        user_prompt: str,
        expected_json: bool = False
    ) -> tuple[str, str]:
        """
        Executes a reasoning turn.
        Returns (thought_process, final_response).
        """
        if not self._llm:
            return ("LLM offline or unavailable. Using analytical heuristics.", "")

        full_system = (
            f"{system_prompt}\n\n"
            "FORMAT INSTRUCTION:\n"
            "First, output your step-by-step reasoning inside <thought> ... </thought> tags.\n"
            "Then output your final answer directly afterwards."
        )

        try:
            messages = [
                SystemMessage(content=full_system),
                HumanMessage(content=user_prompt)
            ]
            response = self._llm.invoke(messages)
            content = response.content if hasattr(response, "content") else str(response)

            # Extract <thought> tags
            thought = ""
            thought_match = re.search(r"<thought>(.*?)</thought>", content, re.DOTALL | re.IGNORECASE)
            if thought_match:
                thought = thought_match.group(1).strip()
                final_content = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL | re.IGNORECASE).strip()
            else:
                final_content = content.strip()

            if expected_json:
                final_content = self._clean_json_str(final_content)

            return (thought, final_content)

        except Exception as e:
            logger.warning(f"Gemini thinking turn encountered exception: {e}")
            return (f"Encountered connection notice: {e}. Defaulting to verified analytical core.", "")

    def _clean_json_str(self, text: str) -> str:
        """Strips markdown code fences (```json ... ```)"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
