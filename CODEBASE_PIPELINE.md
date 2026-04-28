# ORBIT: Pipeline Architecture

This document provides a highly detailed breakdown of how ORBIT processes user requests, bridges conversational chat with agentic tool execution, and securely executes python plugins.

## 1. The Interaction Loop (`orchestrator.py`)
This is the main entry point to the system. It implements a persistent Read-Eval-Print Loop (REPL) giving the user an interactive CLI experience.

1. **Context Initialization:** When it starts, it automatically creates a `.chats` directory. The `chat_history` list (the memory) is synchronized constantly to an isolated JSON file.
2. **Input Capture:** The `while True` loop captures the user's `goal` from the terminal and appends it to `chat_history` as an Ollama user message.
3. **Execution Delivery:** The `chat_history` is passed instantly to the `Planner`.
4. **Auto-Naming:** On the *very first interaction*, `orchestrator.py` dispatches a separate background request to Ollama to summarize the conversation into a 2-4 word filename, automatically renaming the `.json` dump for optimal history tracking.

## 2. The Central Brain (`core/planner.py`)
This is the core heuristic intelligence of the system. It receives exactly two things: the `chat_history` and a massive string detailing every registered Tool.

**The Streaming Evaluator**
Ollama natively streams its answers token-by-token. The Planner's intelligence resides entirely within its stream parser (`process_goal`):
- As it processes the first a few chunks of the stream, it is looking for a **Mode Identifier**.
- **Mode `<CHAT>`:** If the agent decides no tools are required (e.g. answering "What is 2+2?"), it prefixes `<CHAT>`. The planner instantly reroutes the stream byte-by-byte natively to the terminal `sys.stdout`. The interaction concludes seamlessly.
- **Mode `JSON`:** If the agent decides tools are required (e.g. "Search the web for news"), it suppresses all stdout printing! It buffers the stream quietly until it forms a complete JSON array roadmap containing `[{"tool_name": ...}]`. It structurally validates the JSON output and passes the raw dictionary array back to ORBIT for execution.

## 3. Dynamic State Passing (`core/registry.py` & `core/state_manager.py`)
Because the LLM plans multiple tools up-front in a single roadmap, Step 2 needs to know what Step 1 produces.

- The `StateManager` is a runtime dictionary that holds shared variables across tools.
- When `tool_search` completes, it literally saves its output to the Python dictionary: `state["search_last_result"] = "[output_data]"`.
- The magic happens in the ORBIT loop: before the system invokes a tool (like `tool_bash`), it scans the LLM-generated arguments. If the LLM wrote `"{{search_last_result}}"`, ORBIT interpolates the value out of the `StateManager` natively before the tool even realizes.

## 4. The Plugin Ecosystem (`tools/`)
The `ToolRegistry` is completely un-opinionated. On boot, it dynamically scans the `/tools` directory and imports any file starting with `tool_`. 
This allows hyper-modular scaling.

Each tool must define three attributes:
- `get_name()`: The system identifier.
- `get_description()`: The JSON-schema definition injected automatically into the LLM system prompt.
- `run(state, args)`: The payload execution.

By adhering strictly to this architecture, the entire Assistant operates seamlessly between unstructured human conversation and highly complex, memory-shared, deterministic tool executions!
