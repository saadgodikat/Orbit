import time
from pathlib import Path
from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager

# Import functions from the standalone docmind script
import docmind

class DocMindTool(BaseTool):
    """Tool wrapper for the DocMind documentation generator."""

    @classmethod
    def get_name(cls) -> str:
        return "docmind"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: docmind\n"
            "DESCRIPTION: Generates comprehensive markdown documentation for an entire codebase folder or single file.\n"
            "REQUIRED ARGS:\n"
            "  - target_path (str): Absolute path to directory or file\n"
            "  - mode (str): 'individual' to process one file per doc, 'grouped' to combine small files\n"
            "STATE OUTPUT: Saves result to {{docmind_last_run}} and {{latest_documentation_paths}} after execution."
        )

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        target_path = args.get("target_path")
        mode = args.get("mode", "individual")

        if not target_path:
            print("\033[38;5;196m[ ERROR ]\033[0m DocMind requires 'target_path' argument.")
            return False

        target = Path(target_path).expanduser().resolve()
        
        if not target.exists():
            print(f"\033[38;5;196m[ ERROR ]\033[0m Path not found: {target}")
            return False

        print(f"\033[38;5;39m[ DOCMIND ]\033[0m Processing {target}...")
        
        output_data = {}

        if target.is_file():
            # Process single file (borrowed logic from docmind.py)
            ext = target.suffix.lower()
            lang = docmind.EXTENSION_TO_LANG.get(ext, "text")
            
            if ext not in docmind.CODE_EXTENSIONS and ext not in docmind.DOC_EXTENSIONS:
                print(f"[ WARNING ] Unsupported file: {target}")
                return False

            file_info = {
                "path": str(target),
                "relative": target.name,
                "extension": ext,
                "language": lang,
                "lines": sum(1 for _ in open(target, "r", errors="ignore")),
                "size": target.stat().st_size,
            }
            
            output_dir = target.parent / "_explanations"
            output_dir.mkdir(exist_ok=True)
            
            explanation = docmind.explain_file(file_info)
            verification = docmind.verify_explanation(file_info, explanation)
            if verification:
                explanation += f"\n\n---\n\n## Verification Report\n\n{verification}"
                
            group = {"name": file_info["relative"], "files": [file_info]}
            md_name = docmind.write_single_explanation(output_dir, group, explanation)
            
            res_path = str(output_dir / md_name)
            output_data["generated_docs"] = [res_path]
            print(f"\033[38;5;114m[ DONE ]\033[0m Saved to {res_path}")

        elif target.is_dir():
            # Process directory
            all_files = docmind.scan_directory(str(target))
            if not all_files:
                print("[ WARNING ] No files found.")
                return False
                
            code_files = [f for f in all_files if f["extension"] not in docmind.DOC_EXTENSIONS]
            doc_files = [f for f in all_files if f["extension"] in docmind.DOC_EXTENSIONS]
            
            if mode == "grouped":
                code_groups = docmind.group_similar(code_files)
            else:
                code_groups = docmind.group_individual(code_files)
                
            output_dir = target / "_explanations"
            output_dir.mkdir(exist_ok=True)
            
            all_groups = []
            generated_paths = []
            
            if doc_files:
                doc_exp = docmind.explain_docs_summary(doc_files)
                doc_group = {"name": "_all_documentation", "files": doc_files}
                md_name = docmind.write_single_explanation(output_dir, doc_group, doc_exp)
                all_groups.append(doc_group)
                generated_paths.append(str(output_dir / md_name))
                
            for group in code_groups:
                explanation = docmind.explain_group(group)
                if len(group["files"]) == 1:
                    verif = docmind.verify_explanation(group["files"][0], explanation)
                    if verif:
                        explanation += f"\n\n---\n\n## Verification Report\n\n{verif}"
                
                md_name = docmind.write_single_explanation(output_dir, group, explanation)
                all_groups.append(group)
                generated_paths.append(str(output_dir / md_name))
                print(f"  \033[38;5;114m✓\033[0m Documented {group['name']}")
                
            docmind.write_index(output_dir, str(target), all_groups, 0)
            generated_paths.append(str(output_dir / "INDEX.md"))
            output_data["generated_docs"] = generated_paths

        # Save success to orchestrator state
        state.set("docmind_last_run", output_data)
        state.set("latest_documentation_paths", output_data.get("generated_docs", []))
        return True
