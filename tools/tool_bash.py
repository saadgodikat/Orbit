import subprocess
from tools.base import BaseTool

class BashTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "tool_bash"

    @classmethod
    def get_description(cls) -> dict:
        return {
            "name": cls.get_name(),
            "description": "Executes raw bash shell commands on the host linux system. Very powerful. Can be used for checking network, curling, system maintenance.",
            "parameters": {
                "command": "The exact bash command to run (e.g. 'curl -I https://example.com' or 'date')"
            }
        }

    def run(self, state, args: dict) -> bool:
        command = args.get("command")
        if not command:
            print("  [tool_bash] Missing 'command'")
            return False

        print(f"  [tool_bash] Executing: {command}")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                out = result.stdout.strip()
                if not out: out = "Command ran successfully with no output."
                state.state["bash_last_result"] = out
                print("  [tool_bash] Saved output to {{bash_last_result}}")
                return True
            else:
                err = result.stderr.strip()
                if not err: err = result.stdout.strip() # Sometimes error is in stdout
                state.state["bash_last_result"] = f"CRITICAL BASH ERROR:\n{err}"
                print(f"  [tool_bash] Command failed. Passed error to LLM context.")
                return True # We still return true so the LLM pipeline reads the output and realizes it failed, and can self-repair!
                
        except Exception as e:
            print(f"  [tool_bash] Exception: {e}")
            return False
