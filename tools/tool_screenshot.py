import os
from typing import Dict, Any
from playwright.sync_api import sync_playwright
from tools.base import BaseTool
from core.state_manager import StateManager

class ScreenshotTool(BaseTool):
    """Tool to capture screenshots from web pages."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_screenshot"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_screenshot\n"
            "DESCRIPTION: Navigates to a web page and captures a full-page screenshot.\n"
            "REQUIRED ARGS:\n"
            "  - url (str): URL to capture\n"
            "  - output_path (str): filename of the image (.png)\n"
            "STATE OUTPUT: None"
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        url = args.get("url")
        raw_output_path = args.get("output_path")

        if not url or not raw_output_path:
            print("\033[38;5;196m[ ERROR ]\033[0m tool_screenshot requires 'url' and 'output_path'.")
            return False

        # Strictly enforce directory
        save_dir = "/home/mohamad-saad-godikat/Pictures/AssistantScreenshot"
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.basename(raw_output_path)
        if not filename.lower().endswith('.png'):
            filename += '.png'
        
        output_path = os.path.join(save_dir, filename)

        print(f"\033[38;5;39m[ SCREENSHOT ]\033[0m Capturing {url} to {output_path}...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                page.screenshot(path=output_path, full_page=True)
                print(f"\033[38;5;114m[ SUCCESS ]\033[0m Screenshot saved to {output_path}")
                browser.close()
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Screenshot failed: {e}")
            return False
