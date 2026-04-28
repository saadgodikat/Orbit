import os
import shutil
from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager

class FileManagerTool(BaseTool):
    """Tool for basic file system manipulation."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_file_manager"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_file_manager\n"
            "DESCRIPTION: Executes a filesystem operation (copy, move, delete, zip).\n"
            "REQUIRED ARGS:\n"
            "  - action (str): One of ['copy', 'move', 'delete', 'zip']\n"
            "  - source_path (str): Absolute file/folder path to operate on\n"
            "  - dest_path (str): (Optional) Target path, required for copy, move, and zip action\n"
            "STATE OUTPUT: Saves status or resulting path to {{file_manager_result}}."
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        action = args.get("action", "").lower()
        source_path = args.get("source_path")
        dest_path = args.get("dest_path")

        if not action or action not in ['copy', 'move', 'delete', 'zip']:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Invalid file manager action: {action}")
            return False
            
        if not source_path or not os.path.exists(source_path):
            print(f"\033[38;5;196m[ ERROR ]\033[0m Source path does not exist: {source_path}")
            return False

        print(f"\033[38;5;39m[ FILE MGR ]\033[0m Executing {action} on {source_path}...")
        
        try:
            if action == 'copy':
                if not dest_path: raise ValueError("dest_path required for copy")
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                else:
                    dname = os.path.dirname(dest_path)
                    if dname: os.makedirs(dname, exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                result = dest_path
                
            elif action == 'move':
                if not dest_path: raise ValueError("dest_path required for move")
                dname = os.path.dirname(dest_path)
                if dname: os.makedirs(dname, exist_ok=True)
                shutil.move(source_path, dest_path)
                result = dest_path
                
            elif action == 'delete':
                if os.path.isdir(source_path):
                    shutil.rmtree(source_path)
                else:
                    os.remove(source_path)
                result = "Deleted"
                
            elif action == 'zip':
                if not dest_path: raise ValueError("dest_path required for zip")
                # dest_path should be path/to/archive (without .zip if make_archive is used)
                base_name = dest_path
                if dest_path.endswith('.zip'):
                    base_name = dest_path[:-4]
                shutil.make_archive(base_name, 'zip', source_path)
                result = f"{base_name}.zip"

            state.set("file_manager_result", result)
            print(f"\033[38;5;114m[ SUCCESS ]\033[0m Operation {action} completed.")
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m File operation failed: {e}")
            return False
