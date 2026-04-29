import psutil
from tools.base import BaseTool

class SysMonitorTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "tool_sys_monitor"

    @classmethod
    def get_description(cls) -> dict:
        return {
            "name": cls.get_name(),
            "description": "Monitors system resources (CPU, Memory) or kills a specific process by name.",
            "parameters": {
                "action": "The action to perform: 'status' or 'kill'.",
                "process_name": "(Optional) The name of the process to kill (required for 'kill')."
            }
        }

    def run(self, state, args: dict) -> bool:
        action = args.get("action", "status")

        try:
            if action == "status":
                cpu_percent = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory()
                
                output = f"CPU Usage: {cpu_percent}%\n"
                output += f"Memory Usage: {mem.percent}% ({mem.used / (1024**3):.1f}GB / {mem.total / (1024**3):.1f}GB)\n"
                
                print(f"  [tool_sys_monitor] \n{output}")
                state.state["sys_monitor_status"] = output
                return True
                
            elif action == "kill":
                process_name = args.get("process_name")
                if not process_name:
                    print("  [tool_sys_monitor] 'process_name' is required for 'kill'")
                    return False
                
                killed_count = 0
                for proc in psutil.process_iter(['pid', 'name']):
                    if process_name.lower() in proc.info['name'].lower():
                        try:
                            proc.kill()
                            killed_count += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass
                
                if killed_count > 0:
                    print(f"  [tool_sys_monitor] Killed {killed_count} processes matching '{process_name}'")
                else:
                    print(f"  [tool_sys_monitor] No processes found matching '{process_name}'")
                    
                state.state["sys_monitor_last_action"] = f"Killed {killed_count} '{process_name}' processes"
                return True
                
            else:
                print(f"  [tool_sys_monitor] Unknown action: {action}")
                return False

        except Exception as e:
            print(f"  [tool_sys_monitor] Error: {e}")
            return False
