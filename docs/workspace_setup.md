# Workspace Setup & Verification Guide: Python/Streamlit Architecture

This document summarizes the workspace configuration created for the **Kaggle AI Agents Capstone Project: Indian Tax Compliance Assistant**.

---

## 1. Directory Structure

We have pivoted the workspace to a Python-heavy backend architecture:

- **`agents/`**: Folder for agent logic (`router_agent.py`, `vision_agent.py`, `calculator_agent.py`).
- **`schemas/`**: Pydantic v2 data models for type-safe validation.
- **`prompts/`**: Reusable text files storing system instructions for the 3 agents.
- **`data/`**: Target folder for user-uploaded tax documents (PDFs, images).
- **`reports/`**: Output directory for generated Markdown and PDF tax compliance reports.
- **`docs/`**: Operational and architecture documentation.
- **`.antigravity/rules/`**: Target directory for Python, PEP 8, GenAI, and Docker rules.
- **`.antigravity/skills/`**: Target directory for workspace custom skills.

---

## 2. Active IDE Rules & Skills (`.antigravity/`)

These configurations are loaded by the IDE to guide coding best practices:

### A. Rules
1. **`python_streamlit_rules.md`**: Enforces Python 3.11+, PEP 8 styling, modern **`google-genai`** SDK usage (strictly prohibiting the legacy `google-generativeai` package), and Streamlit caching/state optimizations.
2. **`logging_docker_rules.md`**: Enforces Stackdriver-compatible logging, robust I/O exception tracebacks, and Cloud Run port/secrets containerization best practices.

### B. Skills
1. **`agent-handoff/SKILL.md`**: Outlines the structured data payload transition between the 3 agents (Router -> Vision -> Calculator) and Pydantic validation steps.

---

## 3. MCP Configuration

Our Standalone Workspace MCP configuration is located under **`.agents/mcp_config.json`**. Only core, helpful servers are kept:

- **`filesystem`**: restricted to Capstone's `data`, `reports`, and `schemas` subdirectories to enforce security.
- **`sequential-thinking`**: active for multi-step reasoning.
- **`memory`**: active to retain session graphs and context.

*Note: The `google-developer-knowledge` MCP is globally active in the IDE.*
