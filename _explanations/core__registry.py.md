# `core/registry.py`

| Property | Value |
|---|---|
| **Language** | python |
| **Lines** | 54 |
| **Size** | 2,128 bytes |
| **Path** | `/home/mohamad-saad-godikat/Desktop/assistant/core/registry.py` |

---

This file defines the `ToolRegistry` class, which is responsible for dynamically discovering and loading all available automation tools from a designated `tools/` directory. It uses Python's `importlib` and `inspect` modules to scan for classes inheriting from `BaseTool`, making them accessible by name at runtime. This pattern allows the system to scale by simply adding new tool modules without modifying the core registry logic.

### Imports
- `import os`: Imports the operating system module, used here for listing directory contents.
- `import sys`: Imports the system-specific parameters and functions, used here to modify `sys.path`.
- `import importlib`: Imports the module used to dynamically load modules by name.
- `import inspect`: Imports the module used to examine live objects, specifically to find classes within a loaded module.
- `from pathlib import Path`: Imports `Path` from the `pathlib` module for object-oriented filesystem path manipulation.
- `from typing import Dict, Type`: Imports typing hints for better code clarity, defining `Dict` (dictionary) and `Type` (type annotation).
- `from tools.base import BaseTool`: Imports the abstract base class that all concrete tools must inherit from.

### Constants / Configuration
(None found)

### Main Block
(No main execution block found)

### Class: `ToolRegistry`
- **Receiver/Class:** ToolRegistry
- **Parameters:** None
- **Returns:** None
- **Line-by-line:**
  > `self.tools: Dict[str, Type[BaseTool]] = {}`
  Initializes an instance attribute `self.tools` as an empty dictionary, which will map tool names (strings) to their corresponding tool classes (`Type[BaseTool]`).
  > `self._load_tools()`
  Calls the private method `_load_tools` immediately upon instantiation to populate the registry with available tools.

### Function: `_load_tools`
- **Receiver/Class:** ToolRegistry
- **Parameters:** None
- **Returns:** None
- **Line-by-line:**
  > `"""Scan the tools/ directory and load all classes inheriting from BaseTool."""`
  This is the docstring explaining the function's purpose.
  > `tools_dir = Path(__file__).parent.parent / "tools"`
  Constructs a `Path` object pointing to the `tools` directory, located two levels up from the current file's directory.
  > `if not tools_dir.exists():`
  Checks if the calculated `tools_dir` path actually exists on the filesystem.
  > `return`
  If the directory does not exist, the method exits early.
  > `# Add project root to path so dynamic imports work`
  A comment indicating the purpose of the following code block.
  > `sys.path.insert(0, str(tools_dir.parent))`
  Prepends the parent directory of the `tools_dir` (which is assumed to be the project root) to `sys.path`, ensuring that dynamic imports can resolve modules correctly.
  > `for filename in os.listdir(tools_dir):`
  Starts iterating over every file and directory name found within the `tools_dir`.
  > `if filename.startswith("tool_") and filename.endswith(".py"):`
  Checks if the current `filename` starts with `"tool_"` AND ends with `".py"`, filtering only relevant tool files.
  > `module_name = f"tools.{filename[:-3]}"`
  Constructs the fully qualified Python module name string (e.g., if the file is `tool_utils.py`, the module name becomes `tools.tool_utils`).
  > `try:`
  Starts a `try` block to handle potential import errors for the module.
  > `module = importlib.import_module(module_name)`
  Dynamically imports the module specified by `module_name` and assigns the loaded module object to the `module` variable.
  > `# Inspect module for BaseTool subclasses`
  A comment indicating the purpose of the following inspection loop.
  > `for name, obj in inspect.getmembers(module, inspect.isclass):`
  Iterates over all members (`name`, `obj`) within the loaded `module` that are instances of classes.
  > `if issubclass(obj, BaseTool) and obj is not BaseTool:`
  Checks two conditions: 1) Is the current class object (`obj`) a subclass of `BaseTool`? AND 2) Is the class object *not* `BaseTool` itself (to avoid registering the base class)?
  > `try:`
  Starts a nested `try` block to handle potential issues when retrieving the tool name.
  > `tool_name = obj.get_name()`
  Calls the `get_name()` method on the class object to retrieve its designated name identifier.
  > `self.tools[tool_name] = obj`
  Registers the class object (`obj`) into the `self.tools` dictionary using the retrieved `tool_name` as the key.
  > `except NotImplementedError:`
  Catches a `NotImplementedError` if `obj.get_name()` fails for a specific tool.
  > `pass`
  Silently ignores the error and continues processing other tools.
  > `except Exception as e:`
  Catches any other general exception that occurs during the loading or inspection of the module.
  > `print(f"\033[38;5;196m[ ERROR ]\033[0m Failed to load tool {filename}: {e}")`
  Prints a formatted error message to the console, indicating which tool failed to load and why.

### Function: `get_tool`
- **Receiver/Class:** ToolRegistry
- **Parameters:**
    - `name` (`str`): The string identifier name of the tool to retrieve.
- **Returns:** `Type[BaseTool]` or `None`: The class type of the requested tool, or `None` if no tool with that name exists.
- **Line-by-line:**
  > `"""Get a tool class by its name identifier."""`
  This is the docstring explaining the function's purpose.
  > `return self.tools.get(name)`
  Uses the dictionary's `.get()` method to safely retrieve the class associated with the given `name`; returns `None` if the key is missing.

### Function: `get_all_tool_descriptions`
- **Receiver/Class:** ToolRegistry
- **Parameters:** None
- **Returns:** `str`: A single, formatted string containing the description of every registered tool, separated by double newlines.
- **Line-by-line:**
  > `"""Get a formatted string of all tools and their descriptions for the LLM."""`
  This is the docstring explaining the function's purpose.
  > `desc = []`
  Initializes an empty list named `desc` to collect all tool descriptions.
  > `for name, tool_cls in self.tools.items():`
  Starts iterating over all key-value pairs (name and class) stored in the `self.tools` dictionary.
  > `desc.append(tool_cls.get_description())`
  Calls the `get_description()` method on the current tool class (`tool_cls`) and appends the returned description string to the `desc` list.
  > `return "\n\n".join(desc)`
  Joins all collected description strings in the `desc` list into a single string, using `\n\n` (two newlines) as the separator between each tool's description.

### Function: `has_tool`
- **Receiver/Class:** ToolRegistry
- **Parameters:**
    - `name` (`str`): The string identifier name to check for existence.
- **Returns:** `bool`: `True` if a tool with the given name exists in the registry, otherwise `False`.
- **Line-by-line:**
  > `"""Check if a tool exists in the registry."""`
  This is the docstring explaining the function's purpose.
  > `return name in self.tools`
  Uses the `in` operator to check for the presence of the provided `name` key within the `self.tools` dictionary and returns the resulting boolean value.

***

**Key Takeaways:**
1. The `ToolRegistry` centralizes tool management, abstracting away the complexity of dynamic module loading.
2. Tool discovery relies on convention: files must be in `tools/`, start with `tool_`, and end with `.py`.
3. The registry uses `sys.path` manipulation to ensure that imported modules can correctly reference the project root.
4. The system provides specific methods (`get_tool`, `has_tool`, `get_all_tool_descriptions`) to interact with the loaded tools safely.

---

## Verification Report

- [x] `__init__` — covered
- [x] `_load_tools` — covered
- [x] `get_tool` — covered
- [x] `get_all_tool_descriptions` — covered
- [x] `has_tool` — covered

VERDICT: COMPLETE