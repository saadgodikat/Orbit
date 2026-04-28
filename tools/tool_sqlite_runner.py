import sqlite3
import json
from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager

class SqliteRunnerTool(BaseTool):
    """Tool to execute SQLite queries."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_sqlite_runner"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_sqlite_runner\n"
            "DESCRIPTION: Executes a SQL query against a local SQLite database.\n"
            "REQUIRED ARGS:\n"
            "  - db_path (str): The absolute path to the .db or .sqlite file\n"
            "  - query (str): The SQL query string to run\n"
            "STATE OUTPUT: Saves resulting rows as a JSON array to {{sqlite_runner_result}}."
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        db_path = args.get("db_path")
        query = args.get("query")

        if not db_path or not query:
            print("\033[38;5;196m[ ERROR ]\033[0m tool_sqlite_runner requires 'db_path' and 'query'.")
            return False

        print(f"\033[38;5;39m[ SQLITE ]\033[0m Running query on {db_path}...")
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query)
            
            # Check if it was a SELECT or modifying query
            if query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("PRAGMA"):
                rows = [dict(row) for row in cursor.fetchall()]
                state.set("sqlite_runner_result", rows)
                print(f"\033[38;5;114m[ SUCCESS ]\033[0m Query returned {len(rows)} rows.")
            else:
                conn.commit()
                msg = f"{cursor.rowcount} row(s) affected."
                state.set("sqlite_runner_result", msg)
                print(f"\033[38;5;114m[ SUCCESS ]\033[0m {msg}")
                
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m SQLite execution failed: {e}")
            state.set("sqlite_runner_result", str(e))
            return False
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Unknown error in SQLite runner: {e}")
            return False
