from app.config.departments import (
    DEPARTMENTS,
    PINECONE_INDEX_NAME
)

from app.retrieval.pinecone_retriever import (
    PineconeRetriever
)

from app.agents.hr.agent import HRAgent
from app.agents.finance.agent import FinanceAgent
from app.agents.sales.agent import SalesAgent


AGENT_CLASSES = {

    "hr": HRAgent,

    "finance": FinanceAgent,

    "sales": SalesAgent

}


def create_agent(department: str):

    department = department.lower().strip()

    if department not in DEPARTMENTS:

        raise ValueError(
            f"Unknown department: {department}"
        )

    config = DEPARTMENTS[department]

    # Create department-specific retriever
    retriever = PineconeRetriever(
        index_name=PINECONE_INDEX_NAME,
        namespace=config.namespace,
        top_k=5

    )

    # Get correct agent class
    agent_class = AGENT_CLASSES[department]

    # Create agent
    agent = agent_class(
        department_name=config.name,
        retriever=retriever,
        relevance_threshold=0.30,
        top_k=5
    )

    return agent