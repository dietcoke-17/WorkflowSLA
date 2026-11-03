"""
WorkflowSLA: Configuration Module
Handles environment variables, default financial parameters, and paths.
"""
import os
import sys
from pathlib import Path

# Ensure vendor directory is in python path
ROOT_DIR = Path(__file__).resolve().parent
VENDOR_DIR = ROOT_DIR / "vendor"
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

# Base directory
BASE_DIR = ROOT_DIR

# Database configuration
is_serverless = os.getenv("VERCEL") is not None or os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
if is_serverless and not os.getenv("DATABASE_URL"):
    default_db_path = "/tmp/workflowsla.db"
else:
    default_db_path = f"{ROOT_DIR}/workflowsla.db"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

# Server configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Financial Simulation Defaults (Phase 3 specs)
DEFAULT_AVERAGE_ORDER_VALUE = float(os.getenv("DEFAULT_AVERAGE_ORDER_VALUE", "45.0"))
DEFAULT_DAILY_TRANSACTIONS = int(os.getenv("DEFAULT_DAILY_TRANSACTIONS", "10000"))
DEFAULT_REVENUE_DROP_PER_HOUR = float(os.getenv("DEFAULT_REVENUE_DROP_PER_HOUR", "0.005"))  # 0.5% per hour
DEFAULT_OPERATIONAL_COST_PER_HOUR = float(os.getenv("DEFAULT_OPERATIONAL_COST_PER_HOUR", "65.0"))
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")

