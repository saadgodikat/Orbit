import json
import urllib.request
import urllib.error
from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager

class ApiCallerTool(BaseTool):
    """Tool to make HTTP requests to JSON APIs."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_api_caller"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_api_caller\n"
            "DESCRIPTION: Makes a basic HTTP request (GET/POST) to an API endpoint and returns JSON.\n"
            "REQUIRED ARGS:\n"
            "  - url (str): the exact https URL to call\n"
            "  - method (str): GET or POST\n"
            "  - headers (dict): (Optional) dictionary of HTTP headers\n"
            "  - payload (dict): (Optional) dictionary representing the request body for POST\n"
            "STATE OUTPUT: Saves response JSON to {{api_caller_result}} after execution."
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        url = args.get("url")
        method = args.get("method", "GET").upper()
        headers = args.get("headers", {})
        payload = args.get("payload")

        if not url:
            print("\033[38;5;196m[ ERROR ]\033[0m tool_api_caller requires 'url'.")
            return False

        print(f"\033[38;5;39m[ API CALLER ]\033[0m {method} {url}...")
        
        try:
            data = None
            if payload:
                if not isinstance(payload, dict):
                    print("\033[38;5;196m[ ERROR ]\033[0m payload must be a JSON dictionary.")
                    return False
                data = json.dumps(payload).encode('utf-8')
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/json"

            if "User-Agent" not in headers:
                headers["User-Agent"] = "Mozilla/5.0 Orchestrator-Agent"

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req) as response:
                result = response.read().decode('utf-8')
                
                # Attempt to parse json
                try:
                    json_result = json.loads(result)
                    state.set("api_caller_result", json_result)
                except json.JSONDecodeError:
                    # Fallback if the response is valid string but not JSON
                    state.set("api_caller_result", result)
                    
                print(f"\033[38;5;114m[ SUCCESS ]\033[0m Received status {response.status}")
                return True
                
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}"
            print(f"\033[38;5;196m[ ERROR ]\033[0m API Error: {error_msg}")
            state.set("api_caller_error", error_msg)
            return False
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m API Request failed: {e}")
            return False
