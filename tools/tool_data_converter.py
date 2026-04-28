import json
import csv
from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager
from io import StringIO

class DataConverterTool(BaseTool):
    """Tool for format conversion like JSON to CSV/MD."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_data_converter"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_data_converter\n"
            "DESCRIPTION: Converts a JSON array of objects to Markdown table or CSV format.\n"
            "REQUIRED ARGS:\n"
            "  - data (list): The JSON array (list of dicts) to convert\n"
            "  - to_format (str): Target format, 'markdown' or 'csv'\n"
            "STATE OUTPUT: Saves string output to {{data_converter_result}}."
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        data = args.get("data")
        to_format = args.get("to_format", "").lower()

        if not data or not isinstance(data, list) or not isinstance(data[0], dict):
            print("\033[38;5;196m[ ERROR ]\033[0m tool_data_converter requires 'data' as a non-empty list of dicts.")
            return False

        if to_format not in ['markdown', 'csv']:
            print("\033[38;5;196m[ ERROR ]\033[0m to_format must be 'markdown' or 'csv'.")
            return False

        print(f"\033[38;5;39m[ CONVERTER ]\033[0m Converting JSON to {to_format}...")
        
        try:
            keys = list(data[0].keys())
            
            if to_format == 'markdown':
                header = "| " + " | ".join(keys) + " |"
                separator = "| " + " | ".join(["---"] * len(keys)) + " |"
                rows = [header, separator]
                for item in data:
                    row = "| " + " | ".join(str(item.get(k, "")) for k in keys) + " |"
                    rows.append(row)
                result = "\n".join(rows)
            elif to_format == 'csv':
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data)
                result = output.getvalue()

            state.set("data_converter_result", result)
            print(f"\033[38;5;114m[ SUCCESS ]\033[0m Converted {len(data)} rows.")
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Conversion failed: {e}")
            return False
