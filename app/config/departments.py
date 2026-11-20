import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DepartmentConfig:
    name: str
    namespace: str
    description: str


PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "minor-project-aavenix-policies"
)


DEPARTMENTS = {

    "hr": DepartmentConfig(
        name="HR",
        namespace="hr-policies",
        description=(
            "Human resources, employees, "
            "leave, attendance, recruitment, "
            "benefits and workplace policies."
        )
    ),

    "finance": DepartmentConfig(
        name="Finance",
        namespace="finance-policies",
        description=(
            "Finance, accounting, expenses, "
            "reimbursements, invoices, payments "
            "and financial policies."
        )
    ),

    "sales": DepartmentConfig(
        name="Sales",
        namespace="sales-policies",
        description=(
            "Sales, customers, leads, deals, "
            "pricing, discounts, commissions "
            "and sales policies."
        )
    )
}