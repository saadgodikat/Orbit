import json
import ollama
from typing import List, Dict, Any
from core.registry import ToolRegistry

class Planner:
    """The intelligence layer that converts English goals into functional roadmaps."""

    def __init__(self, registry: ToolRegistry, model: str = "gemma4:e4b"):
        self.registry = registry
        self.model = model

    def process_goal(self, chat_history: List[Dict[str, str]], stream_callback=None) -> Dict[str, Any]:
        tools_desc = self.registry.get_all_tool_descriptions()
        import datetime
        current_time = datetime.datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

        system_prompt = f"""You are the Master Planner for ORBIT.
Your job is to read the user's goal and plan tool executions OR respond directly.
CURRENT SYSTEM DATE AND TIME: {current_time}


AVAILABLE TOOLS:
{tools_desc}

MODES:
<CHAT> — Use when NO tools are needed. Start response EXACTLY with <CHAT>.
         Example: <CHAT> The answer is 42.
         Keep responses concise. No padding.

JSON   — Use when tools ARE needed. Output ONLY a raw JSON array. Nothing else.
         Example: [{{"tool_name": "browser", "args": {{"url": "..."}}, "description": "..."}}]

RULES:
1. Never mix modes. Either <CHAT> or JSON. Never both.
2. JSON must be valid and raw — no backticks, no markdown, no extra text.
3. No generic placeholders like <result> or [insert text]. Be specific.
4. Use {{browser_last_result}} or {{step_N_output}} to pass data between steps.
5. If the goal is impossible with available tools, use <CHAT> to explain why.
6. Never hallucinate a tool that does not exist in AVAILABLE TOOLS.
"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)

        def clean_content(c: str) -> str:
            if c.startswith("```json"):
                c = c[7:]
            elif c.startswith("```"):
                c = c[3:]
            if c.endswith("```"):
                c = c[:-3]
            return c.strip()

        try:
            # Using stream=True directly 
            response = ollama.chat(model=self.model, messages=messages, options={"temperature": 0.2, "num_ctx": 4096}, stream=True)
            
            buffer = ""
            is_chat = False
            is_json = False
            
            for chunk in response:
                token = chunk["message"]["content"]
                
                if not is_chat and not is_json:
                    buffer += token
                    if "<CHAT>" in buffer:
                        is_chat = True
                        clean_start = buffer.split("<CHAT>", 1)[1]
                        if clean_start and stream_callback:
                            stream_callback(clean_start)
                    elif "[" in buffer and len(buffer) > 15:
                        is_json = True
                elif is_chat:
                    if stream_callback:
                        stream_callback(token)
                    buffer += token  # Keep tracking it to return it to history
                elif is_json:
                    buffer += token
                    
            if is_chat:
                return {"type": "chat", "content": buffer.replace("<CHAT>", "").strip()}
                
            content = clean_content(buffer.strip())
            
            try:
                roadmap = json.loads(content)
            except json.JSONDecodeError as e:
                # Fallback: Extract everything between first [ and last ] or first { and last }
                import re
                list_match = re.search(r'\[.*\]', content, re.DOTALL)
                dict_match = re.search(r'\{.*\}', content, re.DOTALL)
                
                parsed = False
                if list_match:
                    try:
                        roadmap = json.loads(list_match.group(0))
                        parsed = True
                    except:
                        pass
                if not parsed and dict_match:
                    try:
                        roadmap = json.loads(dict_match.group(0))
                        parsed = True
                    except:
                        pass
                
                if not parsed:
                    return {"type": "error", "message": f"Invalid JSON generated: {e}\nRaw Output: {content}"}
            
            # --- Structural Validation & Forgiveness ---
            if isinstance(roadmap, dict):
                for key in ["steps", "roadmap", "plan", "actions"]:
                    if key in roadmap and isinstance(roadmap[key], list):
                        roadmap = roadmap[key]
                        break
                else:
                    if "tool_name" in roadmap:
                        roadmap = [roadmap]
                        
            if not isinstance(roadmap, list):
                return {"type": "error", "message": f"Roadmap is not a list. Got: {type(roadmap).__name__}"}
                
            for i, step in enumerate(roadmap):
                if not isinstance(step, dict):
                    return {"type": "error", "message": "Invalid step format"}
                
                required_keys = {"tool_name", "args", "description"}
                missing = required_keys - set(step.keys())
                if missing:
                    return {"type": "error", "message": f"Missing keys: {missing}"}
                    
                if not isinstance(step["tool_name"], str) or not step["tool_name"].strip():
                    return {"type": "error", "message": "Invalid tool_name"}
                    
                if not isinstance(step["args"], dict):
                    return {"type": "error", "message": "Invalid args"}

            return {"type": "roadmap", "steps": roadmap}
            
        except Exception as e:
            return {"type": "error", "message": str(e)}
