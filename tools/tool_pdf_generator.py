import os
from typing import Dict, Any
from playwright.sync_api import sync_playwright
from tools.base import BaseTool
from core.state_manager import StateManager

class PdfGeneratorTool(BaseTool):
    """Tool to generate PDFs from web pages."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_pdf_generator"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_pdf_generator\n"
            "DESCRIPTION: Navigates to a web page or local HTML file and generates a PDF document.\n"
            "REQUIRED ARGS:\n"
            "  - url (str): http web url OR local absolute file path\n"
            "  - output_path (str): filename of the PDF to save as\n"
            "STATE OUTPUT: None"
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        url = args.get("url")
        raw_output_path = args.get("output_path")

        if not url or not raw_output_path:
            print("\033[38;5;196m[ ERROR ]\033[0m tool_pdf_generator requires 'url' and 'output_path'.")
            return False

        # Resolve relative and absolute local paths to file:// URLs
        if not url.startswith(('http://', 'https://', 'file://')):
            url = os.path.abspath(url)
            url = f"file://{url}"
        elif url.startswith('/'):
            url = f"file://{url}"

        # Strictly enforce directory
        save_dir = "/home/mohamad-saad-godikat/Pictures/AssistantPdf"
        os.makedirs(save_dir, exist_ok=True)
        filename = os.path.basename(raw_output_path)
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'
        
        output_path = os.path.join(save_dir, filename)

        print(f"\033[38;5;39m[ PDF GENERATOR ]\033[0m Generating PDF for {url} to {output_path}...")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                page.pdf(
                    path=output_path,
                    format="A4",
                    margin={"top": "20mm", "right": "15mm", "bottom": "20mm", "left": "15mm"},
                    print_background=True,
                )
                print(f"\033[38;5;114m[ SUCCESS ]\033[0m PDF saved to {output_path}")
                browser.close()
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m PDF Generation failed: {e}")
            return False
