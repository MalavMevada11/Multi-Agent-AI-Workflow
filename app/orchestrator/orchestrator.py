from dotenv import load_dotenv

from pydantic import BaseModel, Field
from typing import Literal

from langchain_google_genai import (
    ChatGoogleGenerativeAI
)

from langchain_core.prompts import (
    ChatPromptTemplate
)

load_dotenv()

class RouteQuery(BaseModel):

    category: Literal[
        "hr",
        "finance",
        "sales"
    ] = Field(
        description=(
            "The department related "
            "to the user's query."
        )
    )


def create_orchestrator():

    llm = ChatGoogleGenerativeAI(

        model="gemini-3.8-flash",

        temperature=0

    )

    structured_llm = llm.with_structured_output(
        RouteQuery,
        method="json_schema"
    )

    prompt = ChatPromptTemplate.from_messages([

        (
            "system",
            """
You are a query classification orchestrator.

Your ONLY job is to classify the user's query
into exactly ONE of these categories:

1. hr
2. finance
3. sales

HR:
Questions related to employees, leave,
attendance, recruitment, hiring, onboarding,
benefits, performance, training, workplace
policies, employee policies and HR procedures.

Finance:
Questions related to expenses, reimbursements,
accounting, budgets, invoices, payments,
taxes, financial reports, financial policies
and controls.

Sales:
Questions related to customers, leads, deals,
sales targets, commissions, discounts, pricing,
sales processes and sales policies.

Rules:

- Return exactly ONE category.
- Do not answer the user's question.
- Do not explain your reasoning.
- Choose the category based on the primary
  intent of the user's query.
"""
        ),

        (
            "human",
            "{query}"
        )

    ])

    orchestrator = prompt | structured_llm

    return orchestrator


def route_query(
    orchestrator,
    query: str
):

    result = orchestrator.invoke({
        "query": query
    })

    return result.category