import subprocess
from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager

class GitAutomatorTool(BaseTool):
    """Tool for basic git operations."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_git_automator"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_git_automator\n"
            "DESCRIPTION: Interfaces with the local git repository to run status, add, or commit.\n"
            "REQUIRED ARGS:\n"
            "  - action (str): One of ['status', 'update_all', 'commit']\n"
            "  - repo_path (str): Absolute path to the git repository\n"
            "  - message (str): (Optional) Commit message, required if action is 'commit'\n"
            "STATE OUTPUT: Saves command output to {{git_automator_result}}."
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        action = args.get("action")
        repo_path = args.get("repo_path")
        message = args.get("message", "")

        if not action or not repo_path:
            print("\033[38;5;196m[ ERROR ]\033[0m tool_git_automator requires 'action' and 'repo_path'.")
            return False

        print(f"\033[38;5;39m[ GIT ]\033[0m {action} inside {repo_path}...")
        
        try:
            if action == "status":
                cmd = ["git", "status", "-s"]
            elif action == "update_all":
                cmd = ["git", "add", "."]
            elif action == "commit":
                if not message:
                    print("\033[38;5;196m[ ERROR ]\033[0m commit requires a 'message'.")
                    return False
                cmd = ["git", "commit", "-m", message]
            else:
                return False
                
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=True)
            output = result.stdout.strip() if result.stdout else "Success"
            state.set("git_automator_result", output)
            print(f"\033[38;5;114m[ SUCCESS ]\033[0m {output}")
            return True
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() if e.stderr else str(e)
            print(f"\033[38;5;196m[ ERROR ]\033[0m Git operation failed: {err}")
            state.set("git_automator_result", err)
            return False
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m {e}")
            return False
