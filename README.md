# 🤖 ORBIT

**Autonomous AI-powered CLI agent that decomposes complex goals into structured roadmaps and executes them using modular tool plugins.**

Powered by **Ollama Gemma** for local LLM inference — no cloud APIs needed.

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│                   YOU (Natural Language Goal)        │
│  "Research how APIs work and generate a PDF report" │
└──────────────────────┬──────────────────────────────┘
                       ▼
              ┌────────────────┐
              │       ORBIT    │  ← orchestrator.py
              │   (Entry Point)│
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │    PLANNER     │  ← core/planner.py
              │  (LLM Decomp)  │  Breaks goal into steps
              └───────┬────────┘
                      ▼
              ┌────────────────┐
              │  TOOL REGISTRY │  ← core/registry.py
              │  (Auto-Discover)│  Finds all tool_*.py files
              └───────┬────────┘
                      ▼
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌─────────┐ ┌──────────┐ ┌──────────┐
    │ Tool 1  │ │ Tool 2   │ │ Tool 3   │  ← Sequential execution
    │(Browser)│ │(Report)  │ │(PDF Gen) │
    └─────────┘ └──────────┘ └──────────┘
                                   ▼
                           ┌──────────────┐
                           │  Final Output │
                           │  (PDF, File)  │
                           └──────────────┘
```

### The Pipeline

1. **You provide a goal** in plain English
2. **Planner** (Gemma LLM) decomposes it into a numbered roadmap of tool calls
3. **Orchestrator** executes each step sequentially, passing state between tools
4. **Human-in-the-loop** — each step is shown for approval before execution (auto-approve available)
5. **Self-repair** — if a step fails, the system retries with error context

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) with `gemma4:e4b` model pulled
- Playwright browsers installed

### Setup

```bash
# Clone and enter the project
cd ~/Desktop/assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install ollama playwright markdown Pillow

# Install Playwright browsers
playwright install chromium

# Pull the LLM model
ollama pull gemma4:e4b
```

### Run

```bash
python3 orchestrator.py "Your goal here"
```

### Examples

```bash
# Research and generate PDF
python3 orchestrator.py "Research how APIs work from 5 websites and generate a PDF report"

# Fetch data and create report
python3 orchestrator.py "Fetch users from jsonplaceholder API and create a PDF report"

# File conversion
python3 orchestrator.py "Convert /path/to/image.jpg to PNG format"

# Web automation
python3 orchestrator.py "Go to GitHub trending and list the top 5 repositories"
```

---

## Project Structure

```
assistant/
├── orchestrator.py          # Main entry point — goal → roadmap → execution
├── browser_agent.py         # Standalone browser automation agent (Playwright + LLM)
├── coding_agent.py          # Autonomous coding agent with self-repair
│
├── core/                    # Framework internals
│   ├── planner.py           # LLM-powered goal decomposition
│   ├── registry.py          # Auto-discovers and loads all tool_*.py plugins
│   └── state_manager.py     # Shared key-value state between tools
│
├── tools/                   # Modular tool plugins (auto-registered)
│   ├── base.py              # BaseTool interface — all tools inherit from this
│   ├── tool_api_caller.py   # HTTP API requests (GET, POST, etc.)
│   ├── tool_browser.py      # Web browser agent wrapper
│   ├── tool_coder.py        # Code generation via LLM
│   ├── tool_data_converter.py # JSON ↔ Markdown table conversion
│   ├── tool_docmind.py      # Document analysis and Q&A
│   ├── tool_downloader.py   # File downloads from URLs
│   ├── tool_email_sender.py # Email dispatch
│   ├── tool_file_converter.py # Universal format converter (images, docs, data)
│   ├── tool_file_manager.py # File read/write/delete operations
│   ├── tool_git_automator.py # Git operations (commit, push, etc.)
│   ├── tool_pdf_generator.py # HTML → PDF via Playwright (A4, styled)
│   ├── tool_report_writer.py # Markdown → styled HTML report
│   ├── tool_screenshot.py   # Web page screenshots
│   └── tool_sqlite_runner.py # SQLite database queries
│
└── venv/                    # Python virtual environment
```

---

## Available Tools (14)

| Tool | Description |
|---|---|
| `browser_agent` | Opens a real browser and completes tasks autonomously using LLM |
| `tool_api_caller` | Makes HTTP requests to any API endpoint |
| `tool_coder` | Generates code files using the LLM |
| `tool_data_converter` | Converts JSON arrays to Markdown tables and vice versa |
| `tool_docmind` | Analyzes documents and answers questions about them |
| `tool_downloader` | Downloads files from URLs to local disk |
| `tool_email_sender` | Sends emails via SMTP |
| `file_converter` | **Universal converter** — images (JPG↔PNG↔WEBP↔BMP↔TIFF↔GIF), PDF→DOCX, DOCX→PDF, CSV↔JSON, MD→HTML |
| `tool_file_manager` | Creates, reads, writes, and deletes files |
| `tool_git_automator` | Automates git operations (add, commit, push) |
| `tool_pdf_generator` | Converts HTML files to professional A4 PDFs |
| `tool_report_writer` | Compiles Markdown into styled HTML reports with cover pages |
| `tool_screenshot` | Captures screenshots of web pages |
| `tool_sqlite_runner` | Runs SQL queries on SQLite databases |

---

## How the Research → PDF Pipeline Works

When you ask for web research:

```
1. Browser Agent visits 5+ websites
2. read_page accumulates content from each site into a buffer
3. LLM Refinement synthesizes raw data into clean, structured markdown
   ├── Strips navigation junk, ads, menus
   ├── Deduplicates repeated content
   ├── Organizes into proper sections with headings
   └── Adds a Sources section with URLs
4. Report Writer converts markdown into a styled HTML report
   ├── Professional serif typography (Georgia)
   ├── Formal monochrome design
   └── Proper heading hierarchy
5. PDF Generator prints to A4 PDF with margins
```

---

## Adding New Tools

Create a new file `tools/tool_yourname.py`:

```python
from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager

class YourTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "your_tool_name"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: your_tool_name\n"
            "DESCRIPTION: What this tool does\n"
            "REQUIRED ARGS:\n"
            "  - arg1 (str): Description\n"
            "STATE OUTPUT: What it saves to state"
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        # Your logic here
        state.set("key", "value")  # Share data with other tools
        return True  # or False on failure
```

The registry auto-discovers any `tool_*.py` file — **no registration needed**.

---

## Architecture Details

### State Manager
Shared key-value store that passes data between tools in a pipeline:
```
tool_api_caller → saves {{api_response}} → tool_data_converter reads it
```

### Planner
Uses the Gemma LLM to decompose goals. The LLM sees all available tool descriptions and generates a JSON roadmap:
```json
[
  {"step": 1, "tool": "tool_api_caller", "args": {"url": "..."}, "description": "Fetch data"},
  {"step": 2, "tool": "tool_report_writer", "args": {"content": "{{api_response}}"}, "description": "Write report"},
  {"step": 3, "tool": "tool_pdf_generator", "args": {"url": "..."}, "description": "Generate PDF"}
]
```

### Human-in-the-Loop
Every step is displayed before execution. The orchestrator supports auto-approval mode for trusted pipelines.

---

## License

MIT
