from tools.base import BaseTool
from duckduckgo_search import DDGS

class SearchTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "tool_search"

    @classmethod
    def get_description(cls) -> dict:
        return {
            "name": cls.get_name(),
            "description": "Searches the internet using DuckDuckGo to get up-to-date real-time data, news, and facts.",
            "parameters": {
                "query": "The search term (e.g. 'latest news on artificial intelligence')"
            }
        }

    def run(self, state, args: dict) -> bool:
        query = args.get("query")
        if not query:
            print("  [tool_search] Missing 'query' argument")
            return False

        try:
            print(f"  [tool_search] Searching web for: '{query}'...")
            results = DDGS().text(query, max_results=5)
            
            output = ""
            for i, res in enumerate(results):
                output += f"[{i+1}] {res['title']}\nURL: {res['href']}\nSnippet: {res['body']}\n\n"
            
            if not output.strip():
                output = "No search results found."
                
            state.state["search_last_result"] = output
            print("  [tool_search] Saved search snippet successfully to state variable {{search_last_result}}.")
            return True
            
        except Exception as e:
            print(f"  [tool_search] Failed to search: {e}")
            return False
