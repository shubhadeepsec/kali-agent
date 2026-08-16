#!/usr/bin/env python3
"""pskill — AI-powered pentesting agent. Run directly or via: python -m pskill"""
import sys
import os

# Add repo root to path so `pskill` package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pskill.cli import run
sys.exit(run() or 0)
