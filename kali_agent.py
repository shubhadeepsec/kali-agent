#!/usr/bin/env python3
"""Kali Agent — Autonomous AI OS Controller and Security Agent for Kali Linux."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kali_agent.cli import run
sys.exit(run() or 0)
