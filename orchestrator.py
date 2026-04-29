import os
import sys
import time
import json
import re
from datetime import datetime
from core.state_manager import StateManager
from core.registry import ToolRegistry
from core.planner import Planner
import ollama

CHAT_DIR = ".chats"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_header():
    print("\033[38;5;39m")
    print("┌──────────────────────────────────────────────────────────┐")
    print("│  ORBIT — Central Agent Execution Engine                  │")
    print("└──────────────────────────────────────────────────────────┘")

    print(r"""
  ██████╗ ██████╗ ██████╗ ██╗████████╗
 ██╔═══██╗██╔══██╗██╔══██╗██║╚══██╔══╝
 ██║   ██║██████╔╝██████╔╝██║   ██║   
 ██║   ██║██╔══██╗██╔══██╗██║   ██║   
 ╚██████╔╝██║  ██║██████╔╝██║   ██║   
  ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═╝   ╚═╝   
    """)
    print("\033[0m")
    print("\033[38;5;238m" + "─" * 58 + "\033[0m")

def stream_callback(token: str):
    sys.stdout.write(f"\033[38;5;253m{token}\033[0m")
    sys.stdout.flush()

def main():
    os.makedirs(CHAT_DIR, exist_ok=True)
    clear_screen()
    print_header()
    
    print("\033[1;38;5;14m1.\033[0m New Chat")
    print("\033[1;38;5;244m2.\033[0m Previous Chat\n")
    
    choice = ""
    while choice not in ["1", "2"]:
        choice = input("\033[38;5;250mSelect option: \033[0m").strip()
    
    chat_history = []
    current_chat_file = ""
    chat_title_generated = True  # Default true to prevent renaming loaded files

    if choice == "2":
        chat_files = sorted([f for f in os.listdir(CHAT_DIR) if f.endswith(".json")], key=lambda x: os.path.getmtime(os.path.join(CHAT_DIR, x)), reverse=True)
        if not chat_files:
            print("\033[38;5;244mNo previous chats found. Starting New Chat instead.\033[0m\n")
            choice = "1"
        else:
            print("\n\033[38;5;244m[ PREVIOUS CHATS ]\033[0m")
            for idx, f in enumerate(chat_files[:10]):
                stat = os.stat(os.path.join(CHAT_DIR, f))
                mod_time = datetime.fromtimestamp(stat.st_mtime).strftime('%b %d, %H:%M')
                print(f"  \033[1;38;5;14m{idx + 1}.\033[0m {f}  \033[38;5;240m[{mod_time}]\033[0m")
            
            sel = input("\n\033[38;5;250mSelect chat number (or ENTER to cancel): \033[0m").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(chat_files[:10]):
                current_chat_file = os.path.join(CHAT_DIR, chat_files[int(sel)-1])
                try:
                    with open(current_chat_file, "r") as f:
                        chat_history = json.load(f)
                    print(f"\033[1;38;5;114mSuccessfully loaded {len(chat_history)} messages.\033[0m\n")
                except Exception as e:
                    print(f"\033[1;38;5;196m[ ERROR ]\033[0m Failed to load chat: {e}\nStarting New Chat.")
                    choice = "1"
            else:
                 choice = "1"

    if choice == "1":
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        current_chat_file = os.path.join(CHAT_DIR, f"chat_{timestamp}.json")
        chat_history = []
        chat_title_generated = False  # Track that we need to generate a real name

    print("\033[38;5;244m[ SYSTEM ] Booting core modules...\033[0m")
    state = StateManager()
    state.clear()
    registry = ToolRegistry()
    planner = Planner(registry)
    
    print("\n\033[38;5;238m" + "─"*58 + "\033[0m")
    print("\033[1;38;5;114mReady.\033[0m Type your goals below. Press Ctrl+C to exit.\n")

    def save_history():
        if current_chat_file:
            with open(current_chat_file, "w") as f:
                json.dump(chat_history, f, indent=2)

    while True:
        try:
            goal = input("\033[1;38;5;14mYou:\033[0m ").strip()
            if not goal: continue
            
            chat_history.append({"role": "user", "content": goal})
            save_history()
            
            print("\033[1;38;5;214mAssistant: \033[0m", end="", flush=True)
            result = planner.process_goal(chat_history, stream_callback=stream_callback)
            print("")  # newline
            
            if result.get("type") == "chat":
                content = result.get("content", "")
                chat_history.append({"role": "assistant", "content": "<CHAT>" + content})
                save_history()
                print("\033[38;5;238m" + "─"*58 + "\033[0m")
            elif result.get("type") == "error":
                print(f"\033[1;38;5;196m[ ERROR ]\033[0m Planner computation failed: {result.get('message')}")
            else:
                roadmap = result.get("steps", [])
                if not roadmap:
                    print("\033[1;38;5;196m[ ERROR ]\033[0m Failed to generate a valid roadmap.")
                else:
                    print(f"\n\033[1;38;5;114m[ ROADMAP GENERATED ]\033[0m {len(roadmap)} steps planned.")
                    tool_outputs = []
                    aborted = False
                    
                    for i, step in enumerate(roadmap):
                        print("\033[38;5;238m" + "─"*58 + "\033[0m")
                        tool_name = step.get("tool_name", "UNKNOWN")
                        args = step.get("args", {})
                        
                        for k, v in args.items():
                            if isinstance(v, str):
                                for sk, sv in state.state.items():
                                    exact_key = "{{" + sk + "}}"
                                    if v == exact_key:
                                        args[k] = sv
                                        v = sv
                                    elif isinstance(v, str) and exact_key in v:
                                        v = v.replace(exact_key, str(sv))
                                        args[k] = v
                                
                        desc = step.get("description", "Executing step")
                        print(f"\033[1;38;5;14m[ STEP {i+1}/{len(roadmap)} ]\033[0m {desc}")
                        print(f"\033[38;5;244m  Tool : \033[0m{tool_name}")
                        print(f"\033[38;5;244m  Args : \033[0m{args}")

                        tool_cls = registry.get_tool(tool_name)
                        if not tool_cls:
                            print(f"\033[38;5;196m[ ERROR ]\033[0m Tool '{tool_name}' not found!")
                            break

                        approval = ""
                        while approval not in ["y", "n", "yes", "no", "abort", "cancel"]:
                            approval = input("\n\033[1;38;5;214m[ APPROVE ]\033[0m Execute this step? [y/n] (or type 'abort'): ").strip().lower()

                        if approval in ["abort", "cancel"]:
                            print("\033[38;5;214m  Execution aborted by user.\033[0m")
                            tool_outputs.append(f"Step {i+1} ({tool_name}): Aborted by user.")
                            aborted = True
                            break

                        if approval in ["n", "no"]:
                            print("\033[38;5;240m  Skipped by user.\033[0m")
                            tool_outputs.append(f"Step {i+1} ({tool_name}): Skipped by user.")
                            continue

                        print("\033[38;5;114m  Executing...\033[0m")
                        try:
                            tool_instance = tool_cls()
                            start_time = time.time()
                            success = tool_instance.run(state, args)
                            elapsed = time.time() - start_time
                            
                            if success:
                                print(f"  \033[38;5;114m[ SUCCESS ]\033[0m Step {i+1} completed in {elapsed:.1f}s.")
                                tool_outputs.append(f"Step {i+1} ({tool_name}): Success in {elapsed:.1f}s.")
                            else:
                                print(f"  \033[38;5;196m[ FAILED ]\033[0m Step {i+1} reported failure.")
                                tool_outputs.append(f"Step {i+1} ({tool_name}): FAILED.")
                                break
                        except Exception as e:
                            print(f"  \033[38;5;196m[ CRASH ]\033[0m Tool {tool_name} crashed: {e}")
                            tool_outputs.append(f"Step {i+1} ({tool_name}): CRASHED with error: {e}")
                            break

                    summary_info = "\n".join(tool_outputs)
                    chat_history.append({"role": "assistant", "content": f"```json\n{json.dumps(roadmap, indent=2)}\n```\nExecution Results:\n{summary_info}"})
                    save_history()

                    print("\033[38;5;238m" + "─"*58 + "\033[0m")
                    if aborted:
                        print("\033[1;38;5;196m[ PIPELINE ABORTED ]\033[0m Returning to prompt.\n")
                    else:
                        print("\033[1;38;5;39m[ PIPELINE COMPLETE ]\033[0m Ready for next request.\n")

            # --- AI Chat Naming (Runs once at the end of the first iteration) ---
            if not chat_title_generated and len(chat_history) >= 2:
                try:
                    name_resp = ollama.chat(model=planner.model, messages=[
                        {"role": "system", "content": "You are a title generator. Return ONLY a 2-4 word lowercase filename describing the topic, separated by underscores. No quotes, no codeblocks. Example: my_cool_project"},
                        {"role": "user", "content": f"Initial message: {chat_history[0]['content']}"}
                    ], options={"temperature": 0.4})
                    raw_name = name_resp["message"]["content"].strip()
                    # Sanitize completely
                    safe_name = re.sub(r'[^a-z0-9_]', '', raw_name.replace(" ", "_").lower())
                    
                    if safe_name:
                        # Append a tiny hash/timestamp if we want, but safe_name is enough if it doesn't exist
                        timestamp = datetime.now().strftime("%M%S")
                        new_chat_file = os.path.join(CHAT_DIR, f"{safe_name}_{timestamp}.json")
                        
                        if os.path.exists(current_chat_file):
                            os.rename(current_chat_file, new_chat_file)
                        current_chat_file = new_chat_file
                        print(f"\033[38;5;240m[ Auto-Saved context to {current_chat_file} ]\033[0m")
                except Exception as e:
                    pass # Silently fail and keep timestamp name if ollama fails
                finally:
                    chat_title_generated = True

        except KeyboardInterrupt:
            print("\n\033[38;5;244mExiting ORBIT...\033[0m")
            sys.exit(0)
        except EOFError:
            print("\n\033[38;5;244mInput stream closed. Exiting ORBIT...\033[0m")
            sys.exit(0)
        except Exception as e:
            print(f"\n\033[1;38;5;196m[ FATAL ERROR ]\033[0m {e}")
            print("\033[38;5;244mAttempting to resume session...\033[0m\n")

if __name__ == "__main__":
    main()
