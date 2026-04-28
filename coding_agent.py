"""
CODING AGENT v2 — An enhanced agentic coding assistant powered by Ollama Gemma.

Features:
- Self-repair loop: auto-retries on command failures with diagnostic guidance
- Enhanced system prompt with few-shot examples optimized for small models
- Context summarization: compresses conversation history to fit context window
- Actions: read/write/edit files, run commands, search files, list dirs
- screenshot_output: renders terminal output as styled images via Pillow
- Auto-detects python3 vs python
- Smarter error handling and recovery
"""

import sys
import os
import json
import shutil
import subprocess
import ollama
from pathlib import Path
from typing import Dict, Any, Optional, List

# ─── Configuration ──────────────────────────────────────────────────────────

MAX_ITERATIONS = 20
MODEL = "gemma4:e4b"
BLOCKED_COMMANDS = ["rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "sudo rm", "chmod 777 /"]
MAX_OUTPUT_LENGTH = 3000          # Truncate long outputs to save context
SUMMARIZE_AFTER = 8              # Summarize conversation after this many iterations
MAX_REPAIR_ATTEMPTS = 2          # Auto-retry failed commands up to N times
COMMAND_TIMEOUT = 300             # Seconds before a command times out

# ─── Auto-detect Python ────────────────────────────────────────────────────

def _detect_python() -> str:
    """Find the correct python executable on this system."""
    for cmd in ["python3", "python"]:
        if shutil.which(cmd):
            return cmd
    return "python3"  # fallback

PYTHON_CMD = _detect_python()

# ─── ANSI Styling ───────────────────────────────────────────────────────────

C_RESET   = "\033[0m"
C_CYAN    = "\033[1;38;5;14m"
C_GREEN   = "\033[1;38;5;114m"
C_RED     = "\033[1;38;5;196m"
C_YELLOW  = "\033[1;38;5;214m"
C_DIM     = "\033[38;5;244m"
C_BLUE    = "\033[38;5;39m"
C_LINE    = "\033[38;5;238m"
C_MAGENTA = "\033[1;38;5;141m"

# ─── System Prompt (Enhanced for small models) ─────────────────────────────

SYSTEM_PROMPT = f"""You are CODER, an expert autonomous coding agent. You complete coding tasks by taking one action at a time.

RESPOND WITH ONLY a single JSON object. No markdown, no explanation, just raw JSON.

AVAILABLE ACTIONS:

1. Read a file:
   {{"action": "read_file", "path": "file.py"}}

2. Write/create a file (always write COMPLETE content):
   {{"action": "write_file", "path": "file.py", "content": "print('hello')"}}

3. Edit a file (find exact text and replace it):
   {{"action": "edit_file", "path": "file.py", "target": "old_text", "replacement": "new_text"}}

4. Run a shell command:
   {{"action": "run_command", "command": "{PYTHON_CMD} file.py"}}

5. Search for text in files (grep):
   {{"action": "search_files", "pattern": "def my_func", "path": "."}}

6. List directory contents:
   {{"action": "list_dir", "path": "."}}

7. Screenshot terminal output (run command and save output as an image):
   {{"action": "screenshot_output", "command": "{PYTHON_CMD} myfile.py", "save_path": "/path/to/screenshot.png"}}
   Supported formats: .png, .jpg, .jpeg. This renders the terminal output as a styled image.

8. Signal completion:
   {{"action": "done", "summary": "Created X and tested it successfully"}}

IMPORTANT RULES:
- Output ONLY valid JSON. No other text.
- One action per response.
- Write COMPLETE, WORKING code with proper imports, error handling, and docstrings.
- ALWAYS use '{PYTHON_CMD}' to run Python files, never 'python'.
- After writing code, ALWAYS run it to verify correctness.
- If a command FAILS, read the error carefully, then fix the code and retry.
- Use search_files to find code in existing files before modifying them.
- To save terminal output as an image, use screenshot_output (NOT scrot or other tools).
- Use the "done" action when finished, with a clear summary.

EXAMPLE WORKFLOW:

Task: "Create a function that reverses a string and test it"

Step 1 → {{"action": "write_file", "path": "reverse.py", "content": "def reverse_string(s):\\n    \\"\\"\\"Reverse a string.\\"\\"\\"\\n    return s[::-1]\\n\\n\\nif __name__ == \\"__main__\\":\\n    tests = [\\"hello\\", \\"\\", \\"a\\", \\"racecar\\"]\\n    for t in tests:\\n        result = reverse_string(t)\\n        print(f\\"reverse_string({{t!r}}) = {{result!r}}\\")"}}
Step 2 → {{"action": "run_command", "command": "{PYTHON_CMD} reverse.py"}}
Step 3 → {{"action": "done", "summary": "Created reverse.py with reverse_string() function and tested it with 4 test cases."}}
"""

# ─── Action Handlers ────────────────────────────────────────────────────────

def handle_read_file(params: Dict[str, Any], work_dir: str) -> str:
    """Read a file and return its contents."""
    path = _resolve_path(params.get("path", ""), work_dir)
    try:
        with open(path, "r") as f:
            content = f.read()
        lines = content.split("\n")
        # Show line numbers for easier editing
        if len(lines) <= 150:
            numbered = "\n".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines))
            return f"[File: {path} | {len(lines)} lines]\n{numbered}"
        else:
            # Truncate large files
            truncated = "\n".join(f"{i+1:4d} | {line}" for i, line in enumerate(lines[:100]))
            return f"[File: {path} | {len(lines)} lines — showing first 100]\n{truncated}\n... ({len(lines) - 100} more lines)"
    except FileNotFoundError:
        return f"ERROR: File not found: {path}"
    except Exception as e:
        return f"ERROR: Could not read file: {e}"


def handle_write_file(params: Dict[str, Any], work_dir: str) -> str:
    """Write content to a file, creating parent directories if needed."""
    path = _resolve_path(params.get("path", ""), work_dir)
    content = params.get("content", "")
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        lines = content.count("\n") + 1
        return f"SUCCESS: Wrote {lines} lines to {path}"
    except Exception as e:
        return f"ERROR: Could not write file: {e}"


def handle_edit_file(params: Dict[str, Any], work_dir: str) -> str:
    """Edit a file by replacing a target string with a replacement."""
    path = _resolve_path(params.get("path", ""), work_dir)
    target = params.get("target", "")
    replacement = params.get("replacement", "")

    if not target:
        return "ERROR: 'target' string cannot be empty."
    
    try:
        with open(path, "r") as f:
            content = f.read()
        
        if target not in content:
            # Give the LLM a hint about what IS in the file
            snippet = content[:500]
            return f"ERROR: Target string not found in {path}.\nHINT — File starts with:\n{snippet}"
        
        count = content.count(target)
        new_content = content.replace(target, replacement, 1)
        
        with open(path, "w") as f:
            f.write(new_content)
        
        return f"SUCCESS: Replaced 1 occurrence in {path}" + (f" ({count - 1} more occurrences remain)" if count > 1 else "")
    except FileNotFoundError:
        return f"ERROR: File not found: {path}"
    except Exception as e:
        return f"ERROR: Could not edit file: {e}"


def handle_run_command(params: Dict[str, Any], work_dir: str) -> str:
    """Execute a shell command with safety checks."""
    command = params.get("command", "")
    
    if not command:
        return "ERROR: No command provided."
    
    # Auto-fix: replace 'python ' with detected python command
    if command.startswith("python ") and PYTHON_CMD != "python":
        command = PYTHON_CMD + command[6:]
    
    # Safety check
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return f"BLOCKED: Command contains forbidden pattern '{blocked}'. Refusing to execute."
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            cwd=work_dir,
        )
        
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        
        if not output.strip():
            output = "(no output)"
        
        # Truncate very long outputs
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH] + f"\n... (truncated, {len(output)} chars total)"
        
        if result.returncode == 0:
            return f"[SUCCESS]\n{output}"
        else:
            return f"[FAILED — exit code {result.returncode}]\n{output}\n\nFIX: Read the error above. Then either edit the file to fix the bug, or write a corrected version."
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {COMMAND_TIMEOUT} seconds. Consider breaking it into smaller steps."
    except Exception as e:
        return f"ERROR: Command execution failed: {e}"


def handle_search_files(params: Dict[str, Any], work_dir: str) -> str:
    """Search for a pattern in files using grep."""
    pattern = params.get("pattern", "")
    path = _resolve_path(params.get("path", "."), work_dir)
    
    if not pattern:
        return "ERROR: No search pattern provided."
    
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=*.py", "--include=*.js", "--include=*.ts",
             "--include=*.html", "--include=*.css", "--include=*.json", "--include=*.md",
             "--include=*.yaml", "--include=*.yml", "--include=*.txt",
             "-I",  # skip binary files
             pattern, path],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=work_dir,
        )
        
        output = result.stdout.strip()
        if not output:
            return f"No matches found for '{pattern}' in {path}"
        
        lines = output.split("\n")
        if len(lines) > 30:
            output = "\n".join(lines[:30]) + f"\n... ({len(lines) - 30} more matches)"
        
        return f"[SEARCH: '{pattern}' — {len(lines)} matches]\n{output}"
    except subprocess.TimeoutExpired:
        return "ERROR: Search timed out."
    except Exception as e:
        return f"ERROR: Search failed: {e}"


def handle_screenshot_output(params: Dict[str, Any], work_dir: str) -> str:
    """Run a command, capture output, and render it as a styled terminal image."""
    command = params.get("command", "")
    save_path = params.get("save_path", "")

    if not command:
        return "ERROR: No command provided."
    if not save_path:
        return "ERROR: No save_path provided. Specify where to save the image."

    # Auto-fix python command
    if command.startswith("python ") and PYTHON_CMD != "python":
        command = PYTHON_CMD + command[6:]

    # Resolve save path
    save_path = _resolve_path(save_path, work_dir)

    # Ensure parent directory exists
    parent = os.path.dirname(save_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    # Ensure valid extension
    ext = os.path.splitext(save_path)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg"]:
        save_path += ".png"
        ext = ".png"

    # Run the command and capture output
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=COMMAND_TIMEOUT, cwd=work_dir,
        )
        output = result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        if not output.strip():
            output = "(no output)"
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {COMMAND_TIMEOUT}s."
    except Exception as e:
        return f"ERROR: Command failed: {e}"

    # Render as terminal-style image using Pillow
    try:
        from PIL import Image, ImageDraw, ImageFont
        import getpass
        import socket

        # Terminal styling (Traditional Linux Terminal)
        BG_COLOR = (48, 10, 36)         # Ubuntu terminal dark aubergine background
        TEXT_COLOR = (255, 255, 255)    # White text
        PROMPT_GREEN = (138, 226, 52)   # Green for user@host
        PROMPT_BLUE = (114, 159, 207)   # Blue for directory
        ERROR_COLOR = (255, 85, 85)     # Red for errors

        # Font
        font_size = 16
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size)
            font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
            font_bold = font

        # Construct prompt
        try:
            user = getpass.getuser()
            host = socket.gethostname()
        except:
            user, host = "user", "linux"
        
        cwd_name = os.path.basename(os.path.abspath(work_dir))
        if os.path.abspath(work_dir) == os.path.expanduser("~"):
            cwd_name = "~"
        else:
            cwd_name = f"~/{cwd_name}"

        lines = output.strip().split("\n")
        
        # Calculate image dimensions
        padding = 10
        line_height = font_size + 6

        # Measure max line width for the image size computation
        dummy_img = Image.new("RGB", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        
        # Calculate prompt width
        prompt_full = f"{user}@{host}:{cwd_name}$ {command}"
        
        max_text_width = 0
        for line in [prompt_full] + lines:
            bbox = dummy_draw.textbbox((0, 0), line, font=font)
            max_text_width = max(max_text_width, bbox[2] - bbox[0])

        img_width = max(max_text_width + padding * 2, 600)
        img_height = (len(lines) + 2) * line_height + padding * 2

        # Create image
        img = Image.new("RGB", (img_width, img_height), BG_COLOR)
        draw = ImageDraw.Draw(img)

        y = padding

        # Draw traditional prompt chunk by chunk to apply colors
        x = padding
        # user@host
        txt = f"{user}@{host}"
        draw.text((x, y), txt, fill=PROMPT_GREEN, font=font_bold)
        x += dummy_draw.textbbox((0, 0), txt, font=font_bold)[2]
        
        # :
        txt = ":"
        draw.text((x, y), txt, fill=TEXT_COLOR, font=font)
        x += dummy_draw.textbbox((0, 0), txt, font=font)[2]

        # directory
        txt = cwd_name
        draw.text((x, y), txt, fill=PROMPT_BLUE, font=font_bold)
        x += dummy_draw.textbbox((0, 0), txt, font=font_bold)[2]

        # $ command
        txt = f"$ {command}"
        draw.text((x, y), txt, fill=TEXT_COLOR, font=font)
        
        y += line_height

        # Draw output lines
        for line in lines:
            text_color = ERROR_COLOR if (exit_code != 0 and ("error" in line.lower() or "traceback" in line.lower())) else TEXT_COLOR
            draw.text((padding, y), line, fill=text_color, font=font)
            y += line_height

        # Save
        if ext in [".jpg", ".jpeg"]:
            img = img.convert("RGB")
            img.save(save_path, "JPEG", quality=95)
        else:
            img.save(save_path, "PNG")

        file_size = os.path.getsize(save_path)
        return f"SUCCESS: Screenshot saved to {save_path} ({_human_size(file_size)}, {img_width}x{img_height}px)"

    except ImportError:
        return "ERROR: Pillow is not installed. Run: pip install Pillow"
    except Exception as e:
        return f"ERROR: Failed to render screenshot: {e}"


def handle_list_dir(params: Dict[str, Any], work_dir: str) -> str:
    """List directory contents."""
    path = _resolve_path(params.get("path", "."), work_dir)
    try:
        entries = sorted(os.listdir(path))
        # Filter out __pycache__ and hidden dirs for cleaner output
        entries = [e for e in entries if not e.startswith(".") and e != "__pycache__"]
        result_lines = []
        for entry in entries:
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                count = len(os.listdir(full))
                result_lines.append(f"  [DIR]  {entry}/  ({count} items)")
            else:
                size = os.path.getsize(full)
                result_lines.append(f"  [FILE] {entry}  ({_human_size(size)})")
        return f"[Directory: {path} | {len(entries)} items]\n" + "\n".join(result_lines)
    except FileNotFoundError:
        return f"ERROR: Directory not found: {path}"
    except Exception as e:
        return f"ERROR: Could not list directory: {e}"


# ─── Helper Functions ───────────────────────────────────────────────────────

def _resolve_path(path: str, work_dir: str) -> str:
    """Resolve a path relative to the working directory."""
    if os.path.isabs(path):
        return path
    return os.path.join(work_dir, path)


def _human_size(nbytes: int) -> str:
    """Convert bytes to a human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if nbytes < 1024:
            return f"{nbytes:.0f}{unit}"
        nbytes /= 1024
    return f"{nbytes:.1f}TB"


def _parse_llm_response(content: str) -> Optional[Dict[str, Any]]:
    """Parse the LLM's JSON response, handling common formatting issues."""
    content = content.strip()
    
    # Strip markdown code fences
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    # Try direct parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try extracting JSON from text
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass
    
    # Try fixing common issues: single quotes → double quotes
    try:
        fixed = content.replace("'", '"')
        return json.loads(fixed)
    except (json.JSONDecodeError, ValueError):
        pass
    
    return None


def _summarize_history(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Compress conversation history to save context window space."""
    if len(messages) <= 4:
        return messages
    
    # Keep system prompt and original task
    system_msg = messages[0]
    task_msg = messages[1]
    
    # Summarize middle messages into a compact recap
    actions_taken = []
    for msg in messages[2:-4]:  # Keep last 4 messages intact
        if msg["role"] == "assistant":
            try:
                action = json.loads(msg["content"])
                a_type = action.get("action", "?")
                if a_type == "write_file":
                    actions_taken.append(f"- Wrote file: {action.get('path', '?')}")
                elif a_type == "read_file":
                    actions_taken.append(f"- Read file: {action.get('path', '?')}")
                elif a_type == "edit_file":
                    actions_taken.append(f"- Edited file: {action.get('path', '?')}")
                elif a_type == "run_command":
                    actions_taken.append(f"- Ran: {action.get('command', '?')}")
                elif a_type == "search_files":
                    actions_taken.append(f"- Searched for: {action.get('pattern', '?')}")
                elif a_type == "list_dir":
                    actions_taken.append(f"- Listed: {action.get('path', '?')}")
            except (json.JSONDecodeError, TypeError):
                pass
    
    recap = "CONTEXT SUMMARY — Here is what you have done so far:\n" + "\n".join(actions_taken) if actions_taken else ""
    
    # Rebuild: system + task + recap + last 4 messages
    compressed = [system_msg, task_msg]
    if recap:
        compressed.append({"role": "user", "content": recap + "\n\nContinue from where you left off."})
    compressed.extend(messages[-4:])
    
    return compressed


# ─── Action Dispatch ────────────────────────────────────────────────────────

ACTION_HANDLERS = {
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "edit_file": handle_edit_file,
    "run_command": handle_run_command,
    "search_files": handle_search_files,
    "screenshot_output": handle_screenshot_output,
    "list_dir": handle_list_dir,
}

ACTION_LABELS = {
    "read_file":         ("→ read_file",         lambda a: a.get("path", "?")),
    "write_file":        ("→ write_file",        lambda a: f"{a.get('path', '?')}  ({a.get('content', '').count(chr(10)) + 1} lines)"),
    "edit_file":         ("→ edit_file",         lambda a: a.get("path", "?")),
    "run_command":       ("→ run_command",       lambda a: f"$ {a.get('command', '?')}"),
    "search_files":      ("→ search_files",      lambda a: f"'{a.get('pattern', '?')}' in {a.get('path', '.')}"),
    "screenshot_output": ("→ screenshot_output", lambda a: f"$ {a.get('command', '?')} → {a.get('save_path', '?')}"),
    "list_dir":          ("→ list_dir",          lambda a: a.get("path", ".")),
}

# ─── Core Agent Loop ───────────────────────────────────────────────────────

def run_agent(task: str, working_dir: str = ".") -> str:
    """
    Run the coding agent on a given task.
    
    Args:
        task: Natural language description of the coding task.
        working_dir: Directory the agent operates in.
        
    Returns:
        A summary string of what the agent accomplished.
    """
    working_dir = os.path.abspath(working_dir)
    os.makedirs(working_dir, exist_ok=True)

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"TASK: {task}\nWORKING DIRECTORY: {working_dir}\n\nBegin by taking the first action."},
    ]

    print(f"\n{C_LINE}{'─' * 60}{C_RESET}")
    print(f"{C_BLUE}  CODING AGENT v2{C_RESET}")
    print(f"{C_DIM}  Model   : {MODEL}{C_RESET}")
    print(f"{C_DIM}  Python  : {PYTHON_CMD}{C_RESET}")
    print(f"{C_DIM}  WorkDir : {working_dir}{C_RESET}")
    print(f"{C_DIM}  Task    : {task}{C_RESET}")
    print(f"{C_LINE}{'─' * 60}{C_RESET}\n")

    final_summary = "Agent did not complete the task."
    consecutive_failures = 0
    parse_errors = 0
    actions_taken = 0

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"{C_CYAN}[ ITERATION {iteration}/{MAX_ITERATIONS} ]{C_RESET} Thinking...")

        # ── Context summarization ──
        if iteration == SUMMARIZE_AFTER and len(messages) > 8:
            old_count = len(messages)
            messages = _summarize_history(messages)
            new_count = len(messages)
            print(f"{C_MAGENTA}  [ CONTEXT ] Compressed {old_count} → {new_count} messages{C_RESET}")

        # ── LLM call ──
        try:
            response = ollama.chat(
                model=MODEL,
                messages=messages,
                options={"temperature": 0.1, "num_ctx": 8192, "num_predict": 4096},
            )
        except Exception as e:
            print(f"{C_RED}[ ERROR ]{C_RESET} Ollama call failed: {e}")
            break

        raw_content = response["message"]["content"].strip()
        action = _parse_llm_response(raw_content)

        # ── Handle parse errors with retry ──
        if action is None:
            parse_errors += 1
            print(f"{C_RED}[ PARSE ERROR {parse_errors} ]{C_RESET} Response is not valid JSON.")
            print(f"{C_DIM}  Raw: {raw_content[:150]}{C_RESET}")
            
            if parse_errors >= 3:
                print(f"{C_RED}[ GIVING UP ]{C_RESET} Too many parse errors. The model is struggling with JSON output.")
                break
            
            messages.append({"role": "assistant", "content": raw_content})
            messages.append({"role": "user", "content": 'INVALID RESPONSE. You must respond with ONLY a JSON object like: {"action": "done", "summary": "..."}\nNo other text. Try again.'})
            continue

        parse_errors = 0  # Reset on successful parse
        action_type = action.get("action", "unknown")

        # ── Handle "done" ──
        if action_type == "done":
            final_summary = action.get("summary", "Task completed.")
            print(f"\n{C_GREEN}[ DONE ]{C_RESET} {final_summary}")
            messages.append({"role": "assistant", "content": raw_content})
            break

        # ── Dispatch action ──
        handler = ACTION_HANDLERS.get(action_type)
        if handler is None:
            result = f"ERROR: Unknown action '{action_type}'. Valid: {', '.join(list(ACTION_HANDLERS.keys()) + ['done'])}"
            print(f"{C_RED}[ UNKNOWN ]{C_RESET} {action_type}")
        else:
            # Pretty-print
            label_info = ACTION_LABELS.get(action_type)
            if label_info:
                label, detail_fn = label_info
                print(f"{C_YELLOW}  {label}{C_RESET}  {detail_fn(action)}")
            
            result = handler(action, working_dir)
            actions_taken += 1
        
        # ── Self-repair: detect failures and guide the LLM ──
        is_failure = result.startswith("[FAILED") or result.startswith("ERROR:")
        
        if is_failure and action_type == "run_command":
            consecutive_failures += 1
            print(f"{C_RED}  ✗ Command failed ({consecutive_failures}/{MAX_REPAIR_ATTEMPTS + 1}){C_RESET}")
            
            if consecutive_failures <= MAX_REPAIR_ATTEMPTS:
                # Inject self-repair guidance
                repair_guidance = (
                    f"\n\nSELF-REPAIR: The command failed. You MUST:\n"
                    f"1. Read the error message above carefully\n"
                    f"2. Read the file that caused the error\n"
                    f"3. Fix the specific bug\n"
                    f"4. Run the command again\n"
                    f"Do NOT rewrite the entire file unless necessary. Use edit_file to fix just the broken part."
                )
                result += repair_guidance
            else:
                print(f"{C_RED}  ✗ Max repair attempts reached. Moving on.{C_RESET}")
                consecutive_failures = 0
        else:
            if not is_failure:
                consecutive_failures = 0  # Reset on success
        
        # Print result preview
        result_preview = result[:300] + ("..." if len(result) > 300 else "")
        print(f"{C_DIM}  Result: {result_preview}{C_RESET}\n")

        # Feed back into conversation
        messages.append({"role": "assistant", "content": raw_content})
        messages.append({"role": "user", "content": f"ACTION RESULT:\n{result}\n\nContinue with the next action, or use 'done' if the task is complete."})

    else:
        print(f"\n{C_RED}[ MAX ITERATIONS ]{C_RESET} Reached {MAX_ITERATIONS} iterations.")
        final_summary = f"Agent reached max iterations ({MAX_ITERATIONS}). {actions_taken} actions were taken."

    print(f"{C_LINE}{'─' * 60}{C_RESET}")
    print(f"{C_DIM}  Stats: {actions_taken} actions | {iteration} iterations | model: {MODEL}{C_RESET}")
    print(f"{C_LINE}{'─' * 60}{C_RESET}")
    return final_summary


# ─── CLI Entry Point ────────────────────────────────────────────────────────

def print_banner():
    print(f"{C_BLUE}")
    print(r"""
     ██████╗ ██████╗ ██████╗ ███████╗██████╗ 
    ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗
    ██║     ██║   ██║██║  ██║█████╗  ██████╔╝
    ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗
    ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║
     ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
    """)
    print(f"{C_RESET}")
    print(f"{C_DIM}  Autonomous Coding Agent v2 — Powered by Ollama Gemma{C_RESET}")
    print(f"{C_DIM}  Self-Repair • Context Compression • Smart Prompting{C_RESET}")
    print(f"{C_LINE}{'─' * 60}{C_RESET}")


def main():
    if len(sys.argv) < 2:
        print_banner()
        print(f"\n{C_RED}[ ERROR ]{C_RESET} Missing task.")
        print(f"{C_DIM}Usage: {PYTHON_CMD} coding_agent.py '<your coding task>'{C_RESET}")
        print(f"{C_DIM}Example: {PYTHON_CMD} coding_agent.py 'Write a Python script that sorts a CSV file'{C_RESET}\n")
        sys.exit(1)

    task = " ".join(sys.argv[1:])

    os.system("cls" if os.name == "nt" else "clear")
    print_banner()

    result = run_agent(task, working_dir=os.getcwd())
    
    print(f"\n{C_GREEN}[ FINAL RESULT ]{C_RESET}")
    print(f"  {result}")
    print()


if __name__ == "__main__":
    main()
