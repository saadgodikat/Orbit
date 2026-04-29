import os
import subprocess
from tools.base import BaseTool

class DndTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "tool_dnd"

    @classmethod
    def get_description(cls) -> dict:
        return {
            "name": cls.get_name(),
            "description": "Toggles 'Do Not Disturb' on Ubuntu (GNOME). Can 'on' or 'off'.",
            "parameters": {
                "state": "The DND state: 'on' or 'off'."
            }
        }

    def run(self, state, args: dict) -> bool:
        mode = args.get("state")
        if not mode or mode not in ["on", "off"]:
            print("  [tool_dnd] Missing or invalid 'state' argument (must be 'on' or 'off')")
            return False

        try:
            # For GNOME: show-banners false means Do Not Disturb is ON
            # show-banners true means Do Not Disturb is OFF
            boolean_value = "false" if mode == "on" else "true"
            
            cmd = f"gsettings set org.gnome.desktop.notifications show-banners {boolean_value}"
            subprocess.run(cmd, shell=True, check=True)
            
            print(f"  [tool_dnd] Set Do Not Disturb to {mode}")
            state.state["dnd_mode"] = mode
            return True

        except Exception as e:
            print(f"  [tool_dnd] Failed to set DND: {e}")
            return False
