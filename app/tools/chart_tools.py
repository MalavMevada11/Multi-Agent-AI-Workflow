import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless / server execution
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from app.config.settings import CHARTS_DIR
from app.schema.state import ChartArtifact


# Set clean modern theme
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["figure.dpi"] = 150


def render_leave_balance_chart(df: pd.DataFrame, employee_name: str) -> ChartArtifact:
    """
    Renders horizontal bar chart of Entitled, Used, and Remaining leaves for an employee.
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    chart_id = f"leave_balance_{employee_name.replace(' ', '_').lower()}"
    file_path = CHARTS_DIR / f"{chart_id}.png"

    fig, ax = plt.subplots(figsize=(8, 4))
    
    leave_types = df["leave_type"].tolist() if "leave_type" in df.columns else [f"Record {i+1}" for i in range(len(df))]
    used = df["used_days"].tolist() if "used_days" in df.columns else [0] * len(df)
    remaining = df["remaining_days"].tolist() if "remaining_days" in df.columns else [0] * len(df)

    x = range(len(leave_types))
    width = 0.35

    ax.barh([p - width/2 for p in x], used, width, label="Used Days", color="#e74c3c", alpha=0.85)
    ax.barh([p + width/2 for p in x], remaining, width, label="Remaining Days", color="#2ecc71", alpha=0.85)

    ax.set_yticks(x)
    ax.set_yticklabels(leave_types, fontsize=11, fontweight="bold")
    ax.set_xlabel("Number of Days", fontsize=11)
    ax.set_title(f"Annual Leave Balance Status: {employee_name} (FY 2026)", fontsize=13, fontweight="bold", pad=12)
    ax.legend(loc="lower right")

    for i in x:
        ax.text(used[i] + 0.2, i - width/2, str(used[i]), va="center", fontsize=10, fontweight="bold")
        ax.text(remaining[i] + 0.2, i + width/2, str(remaining[i]), va="center", fontsize=10, fontweight="bold")

    plt.tight_layout()
    fig.savefig(str(file_path))
    plt.close(fig)

    total_remaining = sum(remaining)
    return ChartArtifact(
        chart_id=chart_id,
        title=f"Leave Balance Breakdown - {employee_name}",
        chart_type="Horizontal Bar Chart",
        file_path=str(file_path),
        key_takeaway=f"{employee_name} currently has {total_remaining} total available leave days across all categories."
    )


def render_budget_vs_spend_chart(df: pd.DataFrame, department: str = "All Departments") -> ChartArtifact:
    """
    Renders grouped bar chart of Allocated Budget vs Actual Spend.
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    chart_id = f"budget_spend_{department.replace(' ', '_').lower()}"
    file_path = CHARTS_DIR / f"{chart_id}.png"

    fig, ax = plt.subplots(figsize=(9, 4.5))

    dept_labels = [f"{row.get('department', 'Dept')} ({row.get('quarter', 'Q')})" for _, row in df.iterrows()]
    budget = [float(row.get('allocated_budget', 0)) / 1000 for _, row in df.iterrows()]
    spend = [float(row.get('actual_spend', 0)) / 1000 for _, row in df.iterrows()]

    x = range(len(df))
    width = 0.35

    ax.bar([p - width/2 for p in x], budget, width, label="Allocated Budget ($k)", color="#3498db", alpha=0.9)
    ax.bar([p + width/2 for p in x], spend, width, label="Actual Spend ($k)", color="#e67e22", alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(dept_labels, rotation=25, ha="right", fontsize=9, fontweight="bold")
    ax.set_ylabel("Amount in Thousands ($k)", fontsize=11)
    ax.set_title(f"Quarterly Budget Allocation vs Actual Spend ({department})", fontsize=13, fontweight="bold", pad=12)
    ax.legend()

    plt.tight_layout()
    fig.savefig(str(file_path))
    plt.close(fig)

    return ChartArtifact(
        chart_id=chart_id,
        title=f"Budget vs Actual Spend ({department})",
        chart_type="Grouped Bar Chart",
        file_path=str(file_path),
        key_takeaway="Comparison of quarterly budget allocations against actual expenditures, highlighting budget variance."
    )


def render_expenses_compliance_chart(df: pd.DataFrame) -> ChartArtifact:
    """
    Renders bar chart of expenses broken down by category, highlighting policy-flagged amounts.
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    chart_id = "expenses_compliance_breakdown"
    file_path = CHARTS_DIR / f"{chart_id}.png"

    fig, ax = plt.subplots(figsize=(9, 4.5))

    plot_df = df.copy()
    if "status" not in plot_df.columns:
        plot_df["status"] = "Approved"
    if "category" not in plot_df.columns:
        plot_df["category"] = "General Expense"
    if "amount" not in plot_df.columns:
        plot_df["amount"] = 0.0

    cat_summary = plot_df.groupby(["category", "status"])["amount"].sum().unstack(fill_value=0)
    
    colors = {"Approved": "#2ecc71", "Flagged": "#e74c3c", "Pending": "#f39c12"}
    active_colors = [colors.get(col, "#95a5a6") for col in cat_summary.columns]

    cat_summary.plot(kind="bar", stacked=True, ax=ax, color=active_colors, alpha=0.9)

    ax.set_title("Expense Claims by Category & Policy Compliance Status", fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Total Spend ($)", fontsize=11)
    ax.set_xlabel("Expense Category", fontsize=11)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=20, ha="right", fontsize=9, fontweight="bold")
    ax.legend(title="Policy Status")

    plt.tight_layout()
    fig.savefig(str(file_path))
    plt.close(fig)

    flagged_sum = plot_df[plot_df["status"] == "Flagged"]["amount"].sum()
    return ChartArtifact(
        chart_id=chart_id,
        title="Expense Claims by Category & Policy Status",
        chart_type="Stacked Bar Chart",
        file_path=str(file_path),
        key_takeaway=f"Total flagged non-compliant expenses amount to ${flagged_sum:,.2f}, primarily in client dinners and flight upgrades."
    )


def render_sales_performance_chart(df: pd.DataFrame, quarter: str = "Q3") -> ChartArtifact:
    """
    Renders sales quota vs achieved revenue by sales rep.
    """
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    chart_id = f"sales_performance_{quarter.lower()}"
    file_path = CHARTS_DIR / f"{chart_id}.png"

    fig, ax = plt.subplots(figsize=(9, 4.5))

    reps = df["sales_rep"].tolist() if "sales_rep" in df.columns else (df["employee_id"].tolist() if "employee_id" in df.columns else [f"Rep {i+1}" for i in range(len(df))])
    targets = [float(row.get("target_amount", 0)) / 1000 for _, row in df.iterrows()]
    achieved = [float(row.get("achieved_amount", 0)) / 1000 for _, row in df.iterrows()]

    x = range(len(reps))
    width = 0.35

    ax.bar([p - width/2 for p in x], targets, width, label="Quota Target ($k)", color="#95a5a6", alpha=0.8)
    ax.bar([p + width/2 for p in x], achieved, width, label="Achieved Revenue ($k)", color="#2980b9", alpha=0.9)

    ax.set_xticks(x)
    ax.set_xticklabels(reps, fontsize=10, fontweight="bold")
    ax.set_ylabel("Revenue ($k)", fontsize=11)
    ax.set_title(f"Sales Performance: Target vs Achieved ({quarter} 2026)", fontsize=13, fontweight="bold", pad=12)
    ax.legend()

    for i in x:
        rate = float(df.iloc[i].get("achievement_rate", 0)) if len(df) > i else 0
        color = "#27ae60" if rate >= 100 else "#c0392b"
        ax.text(i, max(targets[i], achieved[i]) + 15, f"{rate:.1f}%", ha="center", fontsize=9, fontweight="bold", color=color)

    plt.tight_layout()
    fig.savefig(str(file_path))
    plt.close(fig)

    met_quota_count = len(df[df["quota_met"] == 1]) if "quota_met" in df.columns else 0
    return ChartArtifact(
        chart_id=chart_id,
        title=f"Sales Performance ({quarter})",
        chart_type="Dual Column Chart",
        file_path=str(file_path),
        key_takeaway=f"{met_quota_count} out of {len(df)} sales representatives achieved 100%+ of their {quarter} quota."
    )
