import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from app.config.settings import SQLITE_DB_PATH


class StructuredDataRetriever:
    """
    Handles structured data extraction from SQLite database and flat files (CSV/Excel).
    Includes schema inspection and query helpers for HR, Finance, and Sales records.
    """

    def __init__(self, db_path: Path = SQLITE_DB_PATH):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def get_database_schema(self) -> Dict[str, List[str]]:
        """
        Returns all tables and their column names.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        schema = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [f"{col[1]} ({col[2]})" for col in cursor.fetchall()]
            schema[table] = columns

        conn.close()
        return schema

    def execute_query(self, sql_query: str) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
        """
        Executes a SELECT query and returns records as list of dicts and a Pandas DataFrame.
        """
        conn = self.get_connection()
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        records = df.to_dict(orient="records")
        return records, df

    def query_employee_leaves(self, employee_id_or_name: str) -> Tuple[str, List[Dict[str, Any]], pd.DataFrame]:
        """
        Finds leave balances and pending requests for an employee.
        """
        sql = f"""
        SELECT 
            e.employee_id,
            e.name,
            e.department,
            e.role,
            lb.leave_type,
            lb.total_entitled,
            lb.used_days,
            lb.remaining_days,
            lb.fiscal_year
        FROM employees e
        JOIN leave_balances lb ON e.employee_id = lb.employee_id
        WHERE LOWER(e.employee_id) = LOWER('{employee_id_or_name}')
           OR LOWER(e.name) LIKE LOWER('%{employee_id_or_name}%')
        """
        records, df = self.execute_query(sql)
        return sql.strip(), records, df

    def query_department_expenses(self, department: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]], pd.DataFrame]:
        """
        Retrieves expense reports with employee names, highlighting flagged items.
        """
        filter_clause = f"WHERE LOWER(e.department) = LOWER('{department}')" if department and department.lower() != "all" else ""
        sql = f"""
        SELECT 
            exp.expense_id,
            exp.employee_id,
            emp.name as employee_name,
            exp.department,
            exp.category,
            exp.amount,
            exp.expense_date,
            exp.description,
            exp.status,
            exp.pre_approved
        FROM expenses exp
        JOIN employees emp ON exp.employee_id = emp.employee_id
        {filter_clause}
        ORDER BY exp.expense_date DESC
        """
        records, df = self.execute_query(sql)
        return sql.strip(), records, df

    def query_department_budgets(self, department: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]], pd.DataFrame]:
        """
        Retrieves budget allocation vs actual spend.
        """
        filter_clause = f"WHERE LOWER(department) = LOWER('{department}')" if department and department.lower() != "all" else ""
        sql = f"""
        SELECT 
            department,
            quarter,
            allocated_budget,
            actual_spend,
            variance,
            ROUND((actual_spend / allocated_budget) * 100, 2) as utilization_rate
        FROM department_budgets
        {filter_clause}
        ORDER BY department, quarter
        """
        records, df = self.execute_query(sql)
        return sql.strip(), records, df

    def query_sales_performance(self, quarter: str = "Q3") -> Tuple[str, List[Dict[str, Any]], pd.DataFrame]:
        """
        Retrieves sales targets vs achievement and closed deals.
        """
        sql = f"""
        SELECT 
            st.employee_id,
            e.name as sales_rep,
            st.quarter,
            st.target_amount,
            st.achieved_amount,
            st.achievement_rate,
            st.quota_met,
            COALESCE(SUM(c.commission_earned), 0) as total_commissions
        FROM sales_targets st
        JOIN employees e ON st.employee_id = e.employee_id
        LEFT JOIN commissions c ON st.employee_id = c.employee_id
        WHERE st.quarter = '{quarter}'
        GROUP BY st.employee_id, e.name, st.quarter, st.target_amount, st.achieved_amount, st.achievement_rate, st.quota_met
        ORDER BY st.achieved_amount DESC
        """
        records, df = self.execute_query(sql)
        return sql.strip(), records, df

    def load_from_file(self, file_path: str) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
        """
        Loads dataset from CSV or Excel.
        """
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        elif path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        records = df.to_dict(orient="records")
        return records, df
