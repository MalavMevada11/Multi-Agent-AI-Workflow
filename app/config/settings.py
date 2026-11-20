import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"
EXPORTS_DIR = DATA_DIR / "exports"
CHARTS_DIR = EXPORTS_DIR / "charts"
REPORTS_DIR = EXPORTS_DIR / "reports"
SQLITE_DB_PATH = DATA_DIR / "company_data.sqlite"

# Ensure directories exist
for folder in [DATA_DIR, SAMPLES_DIR, EXPORTS_DIR, CHARTS_DIR, REPORTS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# LLM Configuration
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Pinecone Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "minor-project-aavenix-policies")

# Similarity search threshold
POLICY_SIMILARITY_THRESHOLD = float(os.getenv("POLICY_SIMILARITY_THRESHOLD", "0.20"))
POLICY_TOP_K = int(os.getenv("POLICY_TOP_K", "4"))
