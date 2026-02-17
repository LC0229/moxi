#!/usr/bin/env python3
"""
Minimal MongoDB connection test. No moxi imports.
Run from repo root: python scripts/test_mongo_connect.py
Uses MONGODB_URI from .env (or set in shell).
"""
import os
import sys

# Load .env manually so we don't need pydantic
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()
uri = os.environ.get("MONGODB_URI", "").strip()
db_name = os.environ.get("MONGODB_DB_NAME", "test").strip()
if not uri:
    print("No MONGODB_URI in .env or environment. Set it and retry.")
    sys.exit(1)

print("Connecting to MongoDB...")

try:
    from pymongo import MongoClient
    client = MongoClient(uri)
    db = client[db_name]
    db.command("ping")
    print("OK: MongoDB ping succeeded.")
except Exception as e:
    print("FAIL:", e)
    sys.exit(1)
