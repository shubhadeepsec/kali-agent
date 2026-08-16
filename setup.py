"""pskill setup — pip install -e . makes pskill available system-wide."""
from setuptools import setup, find_packages

setup(
    name="pskill",
    version="3.0.0",
    description="AI-powered pentesting agent — like Claude Code, but for hacking",
    author="pskill",
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
            "pskill=pskill.cli:run",
        ],
    },
    package_data={
        "": ["../playbooks/**/*.md"],
    },
)
