from app.agents.base.base_agent import BaseDepartmentAgent
from app.agents.sales.prompt import create_sales_prompt


class SalesAgent(BaseDepartmentAgent):

    def create_prompt(self):

        return create_sales_prompt()