import sqlite3
import os
from tools.base import BaseTool

DB_PATH = "tasks.db"

class TaskManagerTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "tool_task_manager"

    @classmethod
    def get_description(cls) -> dict:
        return {
            "name": cls.get_name(),
            "description": "Manages a local task/to-do list. Can 'add', 'list', 'complete', or 'delete' tasks.",
            "parameters": {
                "action": "The action to perform: 'add', 'list', 'complete', or 'delete'.",
                "title": "(Optional) Title of the task (required for 'add').",
                "task_id": "(Optional) The ID of the task (required for 'complete' and 'delete')."
            }
        }

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        return conn

    def run(self, state, args: dict) -> bool:
        action = args.get("action")
        if not action:
            print("  [tool_task_manager] Missing 'action' argument")
            return False

        conn = self._init_db()
        cursor = conn.cursor()

        try:
            if action == "add":
                title = args.get("title")
                if not title:
                    print("  [tool_task_manager] 'title' is required for 'add'")
                    return False
                
                cursor.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
                conn.commit()
                print(f"  [tool_task_manager] Added task: {title}")
                state.state["task_last_action"] = f"Added task: {title}"
                
            elif action == "list":
                cursor.execute("SELECT id, title, status FROM tasks ORDER BY id ASC")
                tasks = cursor.fetchall()
                if not tasks:
                    print("  [tool_task_manager] No tasks found.")
                    state.state["task_list"] = "No tasks."
                else:
                    output = "To-Do List:\n"
                    for t in tasks:
                        checkbox = "[x]" if t[2] == "completed" else "[ ]"
                        output += f"{checkbox} {t[0]}: {t[1]}\n"
                    print(f"  [tool_task_manager] Found {len(tasks)} tasks.")
                    state.state["task_list"] = output
                    
            elif action == "complete":
                task_id = args.get("task_id")
                if not task_id:
                    print("  [tool_task_manager] 'task_id' is required for 'complete'")
                    return False
                
                cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
                if cursor.rowcount > 0:
                    print(f"  [tool_task_manager] Marked task {task_id} as completed")
                    state.state["task_last_action"] = f"Completed task {task_id}"
                else:
                    print(f"  [tool_task_manager] Task {task_id} not found")
                    return False
                conn.commit()
                
            elif action == "delete":
                task_id = args.get("task_id")
                if not task_id:
                    print("  [tool_task_manager] 'task_id' is required for 'delete'")
                    return False
                
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                if cursor.rowcount > 0:
                    print(f"  [tool_task_manager] Deleted task {task_id}")
                    state.state["task_last_action"] = f"Deleted task {task_id}"
                else:
                    print(f"  [tool_task_manager] Task {task_id} not found")
                    return False
                conn.commit()
            else:
                print(f"  [tool_task_manager] Unknown action: {action}")
                return False

            return True

        except Exception as e:
            print(f"  [tool_task_manager] Error: {e}")
            return False
        finally:
            conn.close()
