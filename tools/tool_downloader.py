import urllib.request
from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager

class DownloaderTool(BaseTool):
    """Tool to download files/images from the internet."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_downloader"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_downloader\n"
            "DESCRIPTION: Downloads a file or image from a given internet URL to a local path.\n"
            "REQUIRED ARGS:\n"
            "  - url (str): URL of the file/image, e.g., 'https://example.com/image.png'\n"
            "  - output_path (str): Local file path to save to, e.g., '/home/user/image.png'\n"
            "STATE OUTPUT: None"
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        import urllib.request
        import re
        
        url_raw = args.get("url", "")
        output_path = args.get("output_path")

        if not url_raw or not output_path:
            print("\033[38;5;196m[ ERROR ]\033[0m tool_downloader requires 'url' and 'output_path' arguments.")
            return False
            
        url = url_raw
        if not url.startswith("http"):
            urls = re.findall(r'(https?://[^\s)\]\'"]+)', url_raw)
            if urls:
                url = urls[0]
            else:
                print("\033[38;5;196m[ ERROR ]\033[0m tool_downloader could not extract a valid HTTP URL from the provided argument.")
                return False

        print(f"\033[38;5;39m[ DOWNLOADER ]\033[0m Downloading {url} to {output_path}...")
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req) as response, open(output_path, 'wb') as out_file:
                chunk = response.read(8192)
                while chunk:
                    out_file.write(chunk)
                    chunk = response.read(8192)
            print(f"\033[38;5;114m[ SUCCESS ]\033[0m Download complete: {output_path}")
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Download failed: {e}")
            return False
