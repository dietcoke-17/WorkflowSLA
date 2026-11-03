"""
WorkflowSLA: Main Application Entrypoint
Run API server, generate synthetic data, or execute analytics reports from the CLI.

Usage:
  python3 main.py               # Starts FastAPI server at http://localhost:8000
  python3 main.py --report      # Runs executive terminal analytics report
  python3 main.py --seed 10000  # Reseeds database with 10,000+ tickets
"""
import sys
import os
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
VENDOR_DIR = ROOT_DIR / "vendor"
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if VENDOR_DIR.exists() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))

import uvicorn
from config import HOST, PORT
from database.connection import init_db
from scripts.generate_synthetic_data import generate_synthetic_dataset
from scripts.run_cli_analytics import print_executive_report


def main():
    parser = argparse.ArgumentParser(description="WorkflowSLA: Cross-Functional Operations & Blockage Tracker")
    parser.add_argument("--report", action="store_true", help="Print executive terminal analytics report")
    parser.add_argument("--seed", type=int, nargs="?", const=10000, help="Seed database with synthetic tickets (default: 10000)")
    parser.add_argument("--host", type=str, default=HOST, help="Server bind host")
    parser.add_argument("--port", type=int, default=PORT, help="Server port")
    args = parser.parse_args()

    init_db()

    if args.report:
        print_executive_report()
        return

    if args.seed:
        generate_synthetic_dataset(target_ticket_count=args.seed)
        return

    print(f"\n=======================================================")
    print(f" Starting WorkflowSLA Server at http://{args.host}:{args.port}")
    print(f" Interactive Dashboard: http://localhost:{args.port}/")
    print(f" API Documentation:    http://localhost:{args.port}/docs")
    print(f" Analysis Endpoint:    http://localhost:{args.port}/analyze-bottlenecks")
    print(f"=======================================================\n")

    uvicorn.run("api.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
