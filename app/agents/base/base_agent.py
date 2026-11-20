from abc import ABC, abstractmethod
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


FALLBACK_RESPONSE = (
    "No information available, talk with the department head"
)

class BaseDepartmentAgent(ABC):

    def __init__(
        self,
        department_name: str,
        retriever,
        relevance_threshold: float = 0.10,
        top_k: int = 5
    ):

        self.department_name = department_name
        self.retriever = retriever

        self.relevance_threshold = relevance_threshold
        self.top_k = top_k

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0
        )

        self.prompt = self.create_prompt()

    @abstractmethod
    def create_prompt(self) -> ChatPromptTemplate:
        """
        Each department provides its own prompt.
        """
        pass

    def retrieve_context(
        self,
        query: str
    ) -> Optional[str]:

        results = self.retriever.retrieve(query)

        if not results:
            return None

        relevant_documents = []

        for document, score in results:

            print(
                f"[{self.department_name}] "
                f"Similarity Score: {score:.4f}"
            )

            if score >= self.relevance_threshold:
                relevant_documents.append(document)

        if not relevant_documents:
            return None

        context_parts = []

        for document in relevant_documents:

            source = document.metadata.get(
                "source",
                "Unknown"
            )

            context_parts.append(
                f"""
                SOURCE: {source}
                CONTENT:
                {document.page_content}
                """
            )

        return "\n\n".join(context_parts)

    def answer(
        self,
        query: str
    ) -> str:

        context = self.retrieve_context(query)

        # No relevant policy found
        if not context:
            return FALLBACK_RESPONSE

        chain = self.prompt | self.llm

        response = chain.invoke({
            "query": query,
            "context": context
        })

        answer = response.content.strip()

        if not answer:
            return FALLBACK_RESPONSE

        return answer