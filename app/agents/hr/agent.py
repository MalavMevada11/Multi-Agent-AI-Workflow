from app.agents.base.base_agent import BaseDepartmentAgent
from app.agents.hr.prompt import create_hr_prompt


class HRAgent(BaseDepartmentAgent):

    def create_prompt(self):

        return create_hr_prompt()