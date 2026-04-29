import os
from datetime import datetime
from tools.base import BaseTool

JOURNAL_DIR = "/home/mohamad-saad-godikat/Pictures/journal"

class NoteTakerTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "tool_note_taker"

    @classmethod
    def get_description(cls) -> dict:
        return {
            "name": cls.get_name(),
            "description": "Appends a quick note or journal entry to today's markdown file.",
            "parameters": {
                "note": "The content of the note to append."
            }
        }

    def run(self, state, args: dict) -> bool:
        note = args.get("note")
        if not note:
            print("  [tool_note_taker] Missing 'note' argument")
            return False

        try:
            if not os.path.exists(JOURNAL_DIR):
                os.makedirs(JOURNAL_DIR, exist_ok=True)
                
            today_str = datetime.now().strftime("%Y-%m-%d")
            time_str = datetime.now().strftime("%H:%M:%S")
            file_path = os.path.join(JOURNAL_DIR, f"{today_str}.md")
            
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(f"## [{time_str}]\n\n{note}\n\n---\n\n")
                
            print(f"  [tool_note_taker] Saved note to {file_path}")
            state.state["note_last_saved"] = file_path
            return True

        except Exception as e:
            print(f"  [tool_note_taker] Error saving note: {e}")
            return False
