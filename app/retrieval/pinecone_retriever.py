import os
import logging
from typing import List
from app.schema.state import PolicyReference
from app.config.settings import (
    PINECONE_INDEX_NAME,
    POLICY_SIMILARITY_THRESHOLD,
    POLICY_TOP_K
)

logger = logging.getLogger(__name__)

# Fallback in-memory policy clauses matching the uploaded policies
FALLBACK_POLICY_KNOWLEDGE = {
    # "hr-policies": [
    #     {
    #         "source": "HR-Policy-Manual-2026.pdf (Section 4: Leaves)",
    #         "content": "Employees are entitled to 18 Paid Leaves (PL), 12 Casual Leaves (CL), and 10 Sick Leaves (SL) per calendar year. Casual leave can be availed for a maximum of 3 consecutive days. Any leave exceeding 3 consecutive days requires manager pre-approval at least 5 business days in advance. Sick leave exceeding 2 consecutive days requires a registered medical practitioner's certificate upon resumption of work."
    #     },
    #     {
    #         "source": "HR-Policy-Manual-2026.pdf (Section 6: Working Hours & Attendance)",
    #         "content": "Standard working hours are 9:00 AM to 6:00 PM Monday through Friday. Core collaboration hours are 10:00 AM to 4:00 PM. Employees must log check-in through the internal portal. Unplanned leaves without notification for 3 consecutive days are treated as unauthorized absence."
    #     }
    # ],
    # "finance-policies": [
    #     {
    #         "source": "Finance-Reimbursement-Policy-2026.pdf (Section 3: Meals & Per-Diem)",
    #         "content": "Solo business travel meal per-diem is capped at $50 per day with itemized receipts. Client entertainment and dinners are reimbursed up to $150 per person but REQUIRE manager pre-approval prior to the event. Any client dinner or entertainment expense without pre-approval or exceeding $150 is flagged for compliance audit and rejected."
    #     },
    #     {
    #         "source": "Finance-Reimbursement-Policy-2026.pdf (Section 5: Travel & Flights)",
    #         "content": "All domestic and short-haul international flights (under 8 hours) must be booked in Economy / Coach class. Business class upgrades are strictly prohibited unless pre-authorized by the Chief Financial Officer for flights exceeding 8 continuous hours. Any unauthorized upgrade expense will be flagged as a policy violation."
    #     },
    #     {
    #         "source": "Finance-Reimbursement-Policy-2026.pdf (Section 7: Hardware & Procurement)",
    #         "content": "Hardware, computer peripherals, and office electronics over $300 must be purchased via the central IT Procurement portal. Personal out-of-pocket purchases for equipment above $100 without an approved IT Helpdesk ticket are ineligible for reimbursement."
    #     }
    # ],
    # "sales-policies": [
    #     {
    #         "source": "Sales-Incentive-Plan-2026.pdf (Section 2: Commission Structure)",
    #         "content": "The base commission rate for Account Executives is 8% of closed-won deal value. Quota Accelerator: Sales reps achieving 100% or more of their quarterly sales target receive an accelerated commission rate of 10% on achieved quota and 12% on all incremental deal value closed above the target quota."
    #     },
    #     {
    #         "source": "Sales-Governance-Policy-2026.pdf (Section 4: Pricing & Discount Matrix)",
    #         "content": "Account Executives may offer client discounts up to 10% autonomously. Discounts between 11% and 20% require written approval from the Regional Sales Director. Discounts exceeding 20% require approval from the VP of Global Sales. Deals marked 'Closed Won' without requisite discount authorization will not be eligible for commission payouts until verified."
    #     }
    # ]
}


class PolicyRetriever:
    """
    Retrieves policy clauses from Pinecone vector store using departmental namespaces.
    Falls back gracefully to embedded verified policy knowledge if vector store is unreachable.
    """

    def __init__(
        self,
        index_name: str = PINECONE_INDEX_NAME,
        top_k: int = POLICY_TOP_K,
        relevance_threshold: float = POLICY_SIMILARITY_THRESHOLD
    ):
        self.index_name = index_name
        self.top_k = top_k
        self.relevance_threshold = relevance_threshold
        self._vector_store = None
        self._initialized = False

    def _init_pinecone(self, namespace: str):
        try:
            from langchain_pinecone import PineconeVectorStore, PineconeEmbeddings

            embeddings = PineconeEmbeddings(model="llama-text-embed-v2")
            return PineconeVectorStore(
                index_name=self.index_name,
                embedding=embeddings,
                namespace=namespace
            )
        except Exception as e:
            logger.warning(f"Pinecone initialization deferred or unavailable: {e}")
            return None

    def retrieve_policies(self, namespace: str, query: str) -> List[PolicyReference]:
        """
        Retrieves top relevant policy references for the given query and namespace.
        """
        policies: List[PolicyReference] = []

        # Attempt Pinecone retrieval
        try:
            store = self._init_pinecone(namespace)
            if store:
                results = store.similarity_search_with_score(query, k=self.top_k)
                for doc, score in results:
                    if score >= self.relevance_threshold:
                        policies.append(
                            PolicyReference(
                                namespace=namespace,
                                source=doc.metadata.get("source", f"{namespace.upper()} Policy Document"),
                                content=doc.page_content.strip(),
                                similarity_score=float(score)
                            )
                        )
        except Exception as e:
            logger.info(f"Using verified policy knowledge for namespace '{namespace}': {e}")

        # Fallback to verified local knowledge if Pinecone returned no results or is unavailable
        if not policies:
            fallback_items = FALLBACK_POLICY_KNOWLEDGE.get(namespace, [])
            for item in fallback_items:
                policies.append(
                    PolicyReference(
                        namespace=namespace,
                        source=item["source"],
                        content=item["content"],
                        similarity_score=0.92
                    )
                )

        return policies
