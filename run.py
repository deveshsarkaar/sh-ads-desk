#!/usr/bin/env python3
"""SH Ads Desk — entry point.  python run.py
Reads HOST / PORT / data-dir from the environment (see .env.example)."""
from app.web import main

if __name__ == "__main__":
    main()
