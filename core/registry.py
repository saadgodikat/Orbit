import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Dict, Type
from tools.base import BaseTool

class ToolRegistry:
    """Dynamically loads and provides access to all available automation tools."""
    
    def __init__(self):
        self.tools: Dict[str, Type[BaseTool]] = {}
        self._load_tools()

    def _load_tools(self) -> None:
        """Scan the tools/ directory and load all classes inheriting from BaseTool."""
        tools_dir = Path(__file__).parent.parent / "tools"
        if not tools_dir.exists():
            return

        # Add project root to path so dynamic imports work
        sys.path.insert(0, str(tools_dir.parent))

        for filename in os.listdir(tools_dir):
            if filename.startswith("tool_") and filename.endswith(".py"):
                module_name = f"tools.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    # Inspect module for BaseTool subclasses
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BaseTool) and obj is not BaseTool:
                            try:
                                tool_name = obj.get_name()
                                self.tools[tool_name] = obj
                            except NotImplementedError:
                                pass
                except Exception as e:
                    print(f"\033[38;5;196m[ ERROR ]\033[0m Failed to load tool {filename}: {e}")

    def get_tool(self, name: str) -> Type[BaseTool]:
        """Get a tool class by its name identifier."""
        return self.tools.get(name)

    def get_all_tool_descriptions(self) -> str:
        """Get a formatted string of all tools and their descriptions for the LLM."""
        desc = []
        for name, tool_cls in self.tools.items():
            info = tool_cls.get_description()
            if isinstance(info, dict):
                tool_str = f"Tool: {info.get('name', name)}\n"
                tool_str += f"Description: {info.get('description', '')}\n"
                params = info.get('parameters', {})
                if params:
                    tool_str += "Parameters:\n"
                    if isinstance(params, dict):
                        for p_name, p_desc in params.items():
                            tool_str += f"  - {p_name}: {p_desc}\n"
                    else:
                        tool_str += f"  {params}\n"
                desc.append(tool_str)
            else:
                desc.append(str(info))
        return "\n\n".join(desc)

    def has_tool(self, name: str) -> bool:
        """Check if a tool exists in the registry."""
        return name in self.tools
