from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager
import browser_agent

class BrowserTool(BaseTool):
    """Tool wrapper for the AI Browser Agent."""

    @classmethod
    def get_name(cls) -> str:
        return "browser_agent"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: browser_agent\n"
            "DESCRIPTION: Opens a real web browser (Playwright) and dynamically agentically completes a task on the web.\n"
            "REQUIRED ARGS:\n"
            "  - task (str): A natural language task description, e.g., 'Go to google and search for latest AI news'\n"
            "STATE OUTPUT: Saves result to {{browser_last_result}} after execution."
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        task = args.get("task")
        if not task:
            print("\033[38;5;196m[ ERROR ]\033[0m browser_agent requires a 'task' argument.")
            return False

        print(f"\033[38;5;39m[ BROWSER AGENT ]\033[0m Handing over control for task: {task}")
        
        try:
            # Reusing the underlying run_agent function which has its own system prompt and ollama loop
            result = browser_agent.run_agent(task)
            
            # Since the browser agent currently just prints and exits when done, 
            # we consider it successful if it didn't throw an error.
            state.set("browser_last_task", task)
            state.set("browser_last_result", result)
            state.set("browser_status", "completed")
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Browser execution failed: {e}")
            return False
