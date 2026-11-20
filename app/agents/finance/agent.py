from app.agents.base.base_agent import BaseDepartmentAgent
from app.agents.finance.prompt import create_finance_prompt


class FinanceAgent(BaseDepartmentAgent):

    def create_prompt(self):

        return create_finance_prompt()