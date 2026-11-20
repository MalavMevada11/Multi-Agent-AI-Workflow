import sys
from pathlib import Path

# Ensure project root is in sys.path so 'app' can always be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
import pandas as pd
from app.config.settings import SQLITE_DB_PATH, SAMPLES_DIR


def generate_synthetic_database(db_path: Path = SQLITE_DB_PATH):
    """
    Creates and populates the enterprise SQLite database with realistic
    tables and records across HR, Finance, and Sales departments.
    Also exports standalone CSV files for demonstration.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # -------------------------------------------------------------
    # 1. EMPLOYEES TABLE
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT NOT NULL,
        joining_date TEXT NOT NULL,
        salary REAL NOT NULL,
        manager_name TEXT
    )
    """)

    employees_data = [
        ("EMP001", "Malav Patel", "Sales", "Senior Account Executive", "malav.patel@company.com", "2023-01-15", 95000, "Rachel Green"),
        ("EMP002", "Priya Iyer", "HR", "Lead HR Business Partner", "priya.iyer@company.com", "2022-03-10", 82000, "David Miller"),
        ("EMP003", "Aarav Sharma", "Finance", "Senior Financial Analyst", "aarav.sharma@company.com", "2022-07-01", 88000, "Sarah Jenkins"),
        ("EMP004", "Rohan Verma", "Sales", "Enterprise Sales Director", "rohan.verma@company.com", "2021-05-18", 125000, "Rachel Green"),
        ("EMP005", "Sneha Rao", "HR", "Talent Acquisition Specialist", "sneha.rao@company.com", "2023-09-01", 65000, "Priya Iyer"),
        ("EMP006", "Vikram Malhotra", "Finance", "Treasury & Accounts Manager", "vikram.m@company.com", "2020-11-12", 105000, "Sarah Jenkins"),
        ("EMP007", "Ananya Deshmukh", "Sales", "Mid-Market Account Executive", "ananya.d@company.com", "2023-04-20", 78000, "Rohan Verma"),
        ("EMP008", "Kabir Khan", "Finance", "Budget & Compliance Auditor", "kabir.khan@company.com", "2022-09-15", 72000, "Vikram Malhotra"),
        ("EMP009", "Neha Kapoor", "HR", "HR Operations & Payroll Lead", "neha.k@company.com", "2021-08-01", 70000, "Priya Iyer"),
        ("EMP010", "Arjun Reddy", "Sales", "Regional Sales Manager (APAC)", "arjun.r@company.com", "2022-02-14", 98000, "Rohan Verma")
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO employees 
    (employee_id, name, department, role, email, joining_date, salary, manager_name)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, employees_data)

    # -------------------------------------------------------------
    # 2. HR: LEAVE BALANCES & REQUESTS
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_balances (
        balance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        leave_type TEXT NOT NULL,
        total_entitled INTEGER NOT NULL,
        used_days INTEGER NOT NULL,
        remaining_days INTEGER NOT NULL,
        fiscal_year INTEGER NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    """)

    leave_balances_data = [
        # Malav Patel (EMP001)
        ("EMP001", "Paid Leave", 18, 6, 12, 2026),
        ("EMP001", "Casual Leave", 12, 7, 5, 2026),
        ("EMP001", "Sick Leave", 10, 2, 8, 2026),
        # Priya Iyer (EMP002)
        ("EMP002", "Paid Leave", 18, 14, 4, 2026),
        ("EMP002", "Casual Leave", 12, 11, 1, 2026),
        ("EMP002", "Sick Leave", 10, 3, 7, 2026),
        # Aarav Sharma (EMP003)
        ("EMP003", "Paid Leave", 18, 9, 9, 2026),
        ("EMP003", "Casual Leave", 12, 4, 8, 2026),
        ("EMP003", "Sick Leave", 10, 1, 9, 2026),
        # Rohan Verma (EMP004)
        ("EMP004", "Paid Leave", 18, 16, 2, 2026),
        ("EMP004", "Casual Leave", 12, 10, 2, 2026),
        ("EMP004", "Sick Leave", 10, 4, 6, 2026),
        # Sneha Rao (EMP005)
        ("EMP005", "Paid Leave", 18, 5, 13, 2026),
        ("EMP005", "Casual Leave", 12, 3, 9, 2026),
        ("EMP005", "Sick Leave", 10, 0, 10, 2026),
        # Vikram Malhotra (EMP006)
        ("EMP006", "Paid Leave", 18, 12, 6, 2026),
        ("EMP006", "Casual Leave", 12, 8, 4, 2026),
        ("EMP006", "Sick Leave", 10, 5, 5, 2026)
    ]

    cursor.executemany("""
    INSERT INTO leave_balances 
    (employee_id, leave_type, total_entitled, used_days, remaining_days, fiscal_year)
    VALUES (?, ?, ?, ?, ?, ?)
    """, leave_balances_data)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leave_requests (
        request_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        leave_type TEXT NOT NULL,
        days_requested INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        status TEXT NOT NULL,
        reason TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    """)

    leave_requests_data = [
        ("LR-101", "EMP001", "Paid Leave", 4, "2026-11-24", "2026-11-27", "Approved", "Family vacation"),
        ("LR-102", "EMP001", "Casual Leave", 1, "2026-10-12", "2026-10-12", "Approved", "Personal errand"),
        ("LR-103", "EMP002", "Casual Leave", 2, "2026-11-03", "2026-11-04", "Approved", "Doctor appointment"),
        ("LR-104", "EMP004", "Paid Leave", 5, "2026-12-21", "2026-12-25", "Pending", "Winter holiday"),
        ("LR-105", "EMP006", "Sick Leave", 3, "2026-09-14", "2026-09-16", "Approved", "Viral fever")
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO leave_requests 
    (request_id, employee_id, leave_type, days_requested, start_date, end_date, status, reason)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, leave_requests_data)

    # -------------------------------------------------------------
    # 3. FINANCE: BUDGETS & EXPENSES
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS department_budgets (
        budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
        department TEXT NOT NULL,
        quarter TEXT NOT NULL,
        allocated_budget REAL NOT NULL,
        actual_spend REAL NOT NULL,
        variance REAL NOT NULL,
        fiscal_year INTEGER NOT NULL
    )
    """)

    budgets_data = [
        ("HR", "Q1", 120000, 114000, 6000, 2026),
        ("HR", "Q2", 125000, 128000, -3000, 2026),
        ("HR", "Q3", 130000, 122000, 8000, 2026),
        ("Finance", "Q1", 95000, 91000, 4000, 2026),
        ("Finance", "Q2", 100000, 104500, -4500, 2026),
        ("Finance", "Q3", 105000, 99000, 6000, 2026),
        ("Sales", "Q1", 280000, 275000, 5000, 2026),
        ("Sales", "Q2", 310000, 325000, -15000, 2026),
        ("Sales", "Q3", 330000, 342000, -12000, 2026)
    ]

    cursor.executemany("""
    INSERT INTO department_budgets 
    (department, quarter, allocated_budget, actual_spend, variance, fiscal_year)
    VALUES (?, ?, ?, ?, ?, ?)
    """, budgets_data)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        expense_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        department TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL,
        pre_approved INTEGER DEFAULT 0,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    """)

    expenses_data = [
        # Normal & compliant expenses
        ("EXP-201", "EMP001", "Sales", "Client Dinner", 120.0, "2026-10-14", "Dinner with Acme Corp prospective buyers", "Approved", 1),
        ("EXP-202", "EMP001", "Sales", "Domestic Flight", 340.0, "2026-10-20", "Travel to Chicago for on-site sales demo", "Approved", 1),
        ("EXP-203", "EMP003", "Finance", "Software Subscription", 450.0, "2026-10-05", "Annual Bloomberg terminal add-on license", "Approved", 1),
        ("EXP-204", "EMP007", "Sales", "Hotel Lodging", 190.0, "2026-10-18", "One night stay at Marriott for client summit", "Approved", 1),
        ("EXP-205", "EMP002", "HR", "Team Offsite Lunch", 280.0, "2026-09-22", "Quarterly HR team lunch (7 people)", "Approved", 1),
        # Expenses with potential policy violations (for policy-compliance detection)
        ("EXP-206", "EMP001", "Sales", "Client Dinner", 210.0, "2026-11-04", "Dinner with VP of GlobalTech without pre-approval", "Flagged", 0),
        ("EXP-207", "EMP004", "Sales", "Business Class Upgrade", 850.0, "2026-11-08", "Flight seat upgrade to Europe", "Flagged", 0),
        ("EXP-208", "EMP008", "Finance", "Office Electronics", 650.0, "2026-11-10", "Noise-cancelling headphones purchased without IT ticket", "Pending", 0),
        ("EXP-209", "EMP010", "Sales", "Ride Sharing / Taxi", 45.0, "2026-11-12", "Airport cab to hotel", "Approved", 1),
        ("EXP-210", "EMP007", "Sales", "Personal Meal Claim", 95.0, "2026-11-14", "Solo room service dinner in hotel (exceeds $50 per-diem limit)", "Flagged", 0)
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO expenses 
    (expense_id, employee_id, department, category, amount, expense_date, description, status, pre_approved)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, expenses_data)

    # -------------------------------------------------------------
    # 4. SALES: TARGETS, DEALS & COMMISSIONS
    # -------------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_targets (
        target_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        quarter TEXT NOT NULL,
        target_amount REAL NOT NULL,
        achieved_amount REAL NOT NULL,
        achievement_rate REAL NOT NULL,
        quota_met INTEGER NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    """)

    targets_data = [
        ("EMP001", "Q3", 250000, 285000, 114.0, 1),
        ("EMP004", "Q3", 500000, 560000, 112.0, 1),
        ("EMP007", "Q3", 180000, 155000, 86.1, 0),
        ("EMP010", "Q3", 300000, 318000, 106.0, 1),
        ("EMP001", "Q2", 240000, 245000, 102.1, 1),
        ("EMP004", "Q2", 480000, 460000, 95.8, 0),
        ("EMP007", "Q2", 170000, 140000, 82.3, 0),
        ("EMP010", "Q2", 290000, 305000, 105.2, 1)
    ]

    cursor.executemany("""
    INSERT INTO sales_targets 
    (employee_id, quarter, target_amount, achieved_amount, achievement_rate, quota_met)
    VALUES (?, ?, ?, ?, ?, ?)
    """, targets_data)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deals (
        deal_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        client_name TEXT NOT NULL,
        deal_value REAL NOT NULL,
        stage TEXT NOT NULL,
        close_date TEXT NOT NULL,
        region TEXT NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
    )
    """)

    deals_data = [
        ("DEAL-301", "EMP001", "Apex Logistics", 95000, "Closed Won", "2026-09-15", "North America"),
        ("DEAL-302", "EMP001", "Zenith Health", 120000, "Closed Won", "2026-09-28", "North America"),
        ("DEAL-303", "EMP001", "Omni Retail", 70000, "Closed Won", "2026-08-11", "North America"),
        ("DEAL-304", "EMP004", "Global Financial Corp", 320000, "Closed Won", "2026-09-20", "Europe"),
        ("DEAL-305", "EMP004", "Starlight Pharma", 240000, "Closed Won", "2026-08-30", "Europe"),
        ("DEAL-306", "EMP007", "Delta Systems", 85000, "Closed Won", "2026-09-12", "North America"),
        ("DEAL-307", "EMP007", "Pacific Cloud", 70000, "Closed Won", "2026-09-29", "North America"),
        ("DEAL-308", "EMP010", "Tokyo Robotics", 180000, "Closed Won", "2026-09-05", "APAC"),
        ("DEAL-309", "EMP010", "Sydney Energy Ltd", 138000, "Closed Won", "2026-09-22", "APAC"),
        ("DEAL-310", "EMP001", "Horizon Media", 50000, "Negotiation", "2026-11-30", "North America")
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO deals 
    (deal_id, employee_id, client_name, deal_value, stage, close_date, region)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, deals_data)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS commissions (
        commission_id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        deal_id TEXT NOT NULL,
        deal_value REAL NOT NULL,
        commission_rate REAL NOT NULL,
        commission_earned REAL NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
        FOREIGN KEY (deal_id) REFERENCES deals(deal_id)
    )
    """)

    commissions_data = [
        ("COMM-401", "EMP001", "DEAL-301", 95000, 0.10, 9500, "Paid"),
        ("COMM-402", "EMP001", "DEAL-302", 120000, 0.12, 14400, "Paid"),
        ("COMM-403", "EMP001", "DEAL-303", 70000, 0.10, 7000, "Paid"),
        ("COMM-404", "EMP004", "DEAL-304", 320000, 0.12, 38400, "Paid"),
        ("COMM-405", "EMP004", "DEAL-305", 240000, 0.12, 28800, "Paid"),
        ("COMM-406", "EMP007", "DEAL-306", 85000, 0.08, 6800, "Paid"),
        ("COMM-407", "EMP010", "DEAL-308", 180000, 0.10, 18000, "Paid")
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO commissions 
    (commission_id, employee_id, deal_id, deal_value, commission_rate, commission_earned, status)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, commissions_data)

    conn.commit()

    # -------------------------------------------------------------
    # EXPORT CSV SAMPLES FOR DEMO / FILE UPLOAD
    # -------------------------------------------------------------
    hr_df = pd.read_sql_query("""
    SELECT e.employee_id, e.name, e.department, lb.leave_type, lb.total_entitled, lb.used_days, lb.remaining_days
    FROM employees e
    JOIN leave_balances lb ON e.employee_id = lb.employee_id
    """, conn)
    hr_df.to_csv(SAMPLES_DIR / "hr_leaves.csv", index=False)

    fin_df = pd.read_sql_query("""
    SELECT expense_id, employee_id, department, category, amount, expense_date, description, status, pre_approved
    FROM expenses
    """, conn)
    fin_df.to_csv(SAMPLES_DIR / "finance_expenses.csv", index=False)

    sales_df = pd.read_sql_query("""
    SELECT d.deal_id, d.employee_id, e.name as sales_rep, d.client_name, d.deal_value, d.stage, d.close_date, d.region
    FROM deals d
    JOIN employees e ON d.employee_id = e.employee_id
    """, conn)
    sales_df.to_csv(SAMPLES_DIR / "sales_performance.csv", index=False)

    conn.close()
    print(f"Database populated at: {db_path}")
    print(f"Sample CSVs exported to: {SAMPLES_DIR}")


if __name__ == "__main__":
    generate_synthetic_database()
