"""kali-agent setup — pip install -e . makes kali-agent available system-wide."""
from setuptools import setup, find_packages

setup(
    name="kali-agent",
    version="0.1.0",
    description="Kali Agent — Autonomous AI OS Controller and Security Agent for Kali Linux",
    author="Kali Agent Team",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0",
        "prompt_toolkit>=3.0",
        "openai>=1.0",
    ],
    extras_require={
        "anthropic": ["anthropic>=0.30"],
    },
    entry_points={
        "console_scripts": [
            "kali-agent=kali_agent.cli:run",
        ],
    },
    package_data={
        "": ["../playbooks/**/*.md"],
    },
)
