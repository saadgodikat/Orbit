from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager
import coding_agent


class CoderTool(BaseTool):
    """Tool wrapper for the autonomous Coding Agent."""

    @classmethod
    def get_name(cls) -> str:
        return "coding_agent"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: coding_agent\n"
            "DESCRIPTION: An autonomous coding agent that can read, write, edit, and execute code files in a specified directory.\n"
            "REQUIRED ARGS:\n"
            "  - task (str): A natural language coding task, e.g., 'Create a Python function that calculates prime numbers'\n"
            "  - working_dir (str): Directory to work in (defaults to .)\n"
            "STATE OUTPUT: Saves result to {{coder_last_result}} after execution."
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        task = args.get("task")
        if not task:
            print("\033[38;5;196m[ ERROR ]\033[0m coding_agent requires a 'task' argument.")
            return False

        working_dir = args.get("working_dir", ".")

        print(f"\033[38;5;39m[ CODING AGENT ]\033[0m Starting autonomous coding for: {task}")

        try:
            result = coding_agent.run_agent(task, working_dir=working_dir)
            
            state.set("coder_last_task", task)
            state.set("coder_last_result", result)
            state.set("coder_status", "completed")
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Coding agent execution failed: {e}")
            state.set("coder_status", f"failed: {e}")
            return False
