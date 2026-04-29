import sqlite3
import os
from datetime import datetime
from tools.base import BaseTool

DB_PATH = "calendar.db"

class CalendarTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "tool_calendar"

    @classmethod
    def get_description(cls) -> dict:
        return {
            "name": cls.get_name(),
            "description": "Manages a local calendar. Can 'add', 'list', or 'delete' events.",
            "parameters": {
                "action": "The action to perform: 'add', 'list', or 'delete'.",
                "title": "(Optional) Title of the event (required for 'add').",
                "date_time": "(Optional) Date and time of the event, e.g., 'YYYY-MM-DD HH:MM' (required for 'add').",
                "description": "(Optional) Description of the event.",
                "event_id": "(Optional) The ID of the event (required for 'delete')."
            }
        }

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date_time TEXT NOT NULL,
                description TEXT
            )
        ''')
        conn.commit()
        return conn

    def run(self, state, args: dict) -> bool:
        action = args.get("action")
        if not action:
            print("  [tool_calendar] Missing 'action' argument")
            return False

        conn = self._init_db()
        cursor = conn.cursor()

        try:
            if action == "add":
                title = args.get("title")
                date_time = args.get("date_time")
                description = args.get("description", "")
                
                if not title or not date_time:
                    print("  [tool_calendar] 'title' and 'date_time' are required for 'add'")
                    return False
                
                cursor.execute("INSERT INTO events (title, date_time, description) VALUES (?, ?, ?)", 
                               (title, date_time, description))
                conn.commit()
                print(f"  [tool_calendar] Added event: {title} at {date_time}")
                state.state["calendar_last_action"] = f"Added event: {title}"
                
            elif action == "list":
                cursor.execute("SELECT id, title, date_time, description FROM events ORDER BY date_time ASC")
                events = cursor.fetchall()
                if not events:
                    print("  [tool_calendar] No upcoming events found.")
                    state.state["calendar_events"] = "No events."
                else:
                    output = "Upcoming Events:\n"
                    for ev in events:
                        output += f"[{ev[0]}] {ev[2]} - {ev[1]} ({ev[3]})\n"
                    print(f"  [tool_calendar] Found {len(events)} events.")
                    state.state["calendar_events"] = output
                    
            elif action == "delete":
                event_id = args.get("event_id")
                if not event_id:
                    print("  [tool_calendar] 'event_id' is required for 'delete'")
                    return False
                
                cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
                if cursor.rowcount > 0:
                    print(f"  [tool_calendar] Deleted event {event_id}")
                    state.state["calendar_last_action"] = f"Deleted event {event_id}"
                else:
                    print(f"  [tool_calendar] Event {event_id} not found")
                    return False
                conn.commit()
            else:
                print(f"  [tool_calendar] Unknown action: {action}")
                return False

            return True

        except Exception as e:
            print(f"  [tool_calendar] Error: {e}")
            return False
        finally:
            conn.close()
