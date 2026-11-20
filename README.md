# 🤖 Multi-Agent AI Workflow for Automated Business Intelligence & Policy Verification

An enterprise-grade, multi-agent AI system that automates the Business Intelligence (BI) lifecycle. Specialized AI agents collaborate to convert raw business data (from SQLite databases and CSV/Excel files) into actionable insights, automated visualizations, and executive reports—while **strictly verifying company policies** stored in a Pinecone vector database across **HR**, **Finance**, and **Sales** departments.

Designed for **executive decision-making**, **employee self-service**, and **live academic/stakeholder presentations**.

---

## 🏗️ System Architecture & Workflow

The workflow follows a 6-stage sequential agent pipeline:

$$\text{User Query} \longrightarrow \text{Coordinator Agent} \longrightarrow \begin{matrix} \text{Policy Retrieval (Pinecone)} \\ \text{Data Retrieval (SQLite / CSV)} \end{matrix} \longrightarrow \begin{matrix} \text{Statistical Analysis \&} \\ \text{Policy Compliance Engine} \end{matrix} \longrightarrow \text{Visualization Agent} \longrightarrow \text{Report Generation Agent}$$

```
                                  ┌────────────────────────┐
                                  │   User / Presentation  │
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │   Coordinator Agent    │
                                  │ (Intent & Dept Router) │
                                  └───────────┬────────────┘
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
        ┌─────────────────────────┐                       ┌─────────────────────────┐
        │ Policy Retrieval Agent  │                       │ Structured Data Agent   │
        │ (Pinecone Vector DB)    │                       │ (SQLite & CSV Loaders)  │
        │ • hr-policies           │                       │ • Employees & Leaves    │
        │ • finance-policies      │                       │ • Budgets & Expenses    │
        │ • sales-policies        │                       │ • Deals & Commissions   │
        └────────────┬────────────┘                       └────────────┬────────────┘
                     └────────────────────────┬────────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   Data Analysis Agent   │
                                 │ • Descriptive Stats     │
                                 │ • Policy Rule Auditor   │
                                 │ • Anomaly Detection     │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   Visualization Agent   │
                                 │ • Matplotlib & Seaborn  │
                                 │ • High-Res Chart PNGs   │
                                 └────────────┬────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │ Report Generation Agent │
                                 │ • Executive Summary     │
                                 │ • KPI Highlight Cards   │
                                 │ • Downloadable PDF      │
                                 └─────────────────────────┘
```

---

## 👥 Specialized Agents

| Agent | Module | Core Responsibilities |
| :--- | :--- | :--- |
| **Coordinator Agent** | `app.agents.coordinator` | Classifies query intent, routes to department (`hr`, `finance`, `sales`), determines mode (Employee Self-Service vs. Executive BI), and broadcasts real-time step events. |
| **Data & Policy Retrieval Agent** | `app.agents.retrieval_agent` | Dual retrieval: queries Pinecone vector database for relevant company policy clauses and executes SQL queries against SQLite or flat CSV files. |
| **Data Analysis & Policy Agent** | `app.agents.analysis_agent` | Calculates statistical KPIs, trends, and aggregates. Audits empirical records against policy thresholds (e.g. meal limits, leave entitlements, commission accelerators) and flags anomalies. |
| **Visualization Agent** | `app.agents.visualization_agent` | Selects appropriate chart types (horizontal bar, grouped spend vs. budget, stacked expense violations, sales quota attainment) and renders publication-ready plots. |
| **Report Generation Agent** | `app.agents.report_agent` | Synthesizes metrics, policy citations, and charts into Markdown summaries and compiles an executive-grade PDF report using ReportLab. |

---

## 🎯 Dual-Audience Use Cases

### 1. Employee Operational Self-Service
- *"How many leaves are left for Malav Patel, and can he take 3 consecutive casual leaves?"*
- *"Can I expense a $180 client dinner without pre-approval?"*
- *Result*: Cross-checks the employee's live database balance with Pinecone policy clauses to provide an immediate, policy-verified decision card.

### 2. Executive Business Intelligence & Policy Audit
- *"Analyze all submitted expenses, check them against reimbursement policy limits, and flag any violations."*
- *"Evaluate quarterly budget allocation versus actual expenditures across departments."*
- *"Review Q3 sales performance against targets and determine commission accelerator eligibility."*
- *Result*: Statistical breakdown, flagged non-compliant transactions, visual comparison charts, and a downloadable executive PDF report.

---

## 🔍 Presentation Feature: Live Agent Step Inspector

Built specifically for live presentations, the Streamlit UI visualizes every intermediate agent step:
1. **Routing**: Department selected, mode assigned, employee identified.
2. **Pinecone Retrieval**: Retrieved document snippets, similarity scores, and policy source citation.
3. **Data Retrieval**: The exact SQL query executed, number of rows retrieved, and raw data preview.
4. **Analysis & Policy Audit**: Computed metrics, policy compliance badge (`COMPLIANT` vs `FLAGGED_VIOLATIONS`), and detected anomalies.
5. **Visualization**: Rendered chart preview and key takeaway insight.
6. **Report**: Formatted report and one-click PDF download.

---

## 🚀 Getting Started

### 1. Prerequisites & Environment Setup
Ensure your `.env` file contains:
```env
GOOGLE_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=minor-project-aavenix-policies
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Enterprise Database & CSVs (Already Done)
To regenerate or reset the synthetic SQLite database and CSV files at any time:
```bash
python -m app.tools.db_generator
```

### 4. Launch the Interactive Presentation UI (Streamlit)
```bash
streamlit run app/ui.py
```

### 5. CLI Execution (Optional)
Run the automated workflow directly from your terminal:
```bash
python app/main.py --query "How many leaves are left for Malav Patel?"
```
Or run the interactive loop:
```bash
python app/main.py
```
