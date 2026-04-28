from pathlib import Path

CODE_EXTENSIONS = [".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php", ".sh"]
DOC_EXTENSIONS = [".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".csv"]
EXTENSION_TO_LANG = {".py": "python", ".js": "javascript", ".ts": "typescript", ".html": "html", ".css": "css", ".md": "markdown", ".json": "json"}

def explain_file(file_info):
    return f"Explanation for {file_info.get('relative', 'file')}"

def verify_explanation(file_info, explanation):
    return "Verification passed."

def write_single_explanation(output_dir, group, explanation):
    name = str(group.get("name", "doc")).replace("/", "_") + ".md"
    path = Path(output_dir) / name
    with open(path, "w") as f:
        f.write(explanation)
    return name

def scan_directory(target_path):
    # Dummy scan that just returns a safe empty list for now
    return []

def group_similar(code_files):
    return [{"name": "group.md", "files": code_files}] if code_files else []

def group_individual(code_files):
    return [{"name": f["relative"], "files": [f]} for f in code_files]

def explain_docs_summary(doc_files):
    return "Summary of documentation files."

def explain_group(group):
    return f"Explanation for group {group.get('name')}"

def write_index(output_dir, target, all_groups, num):
    path = Path(output_dir) / "INDEX.md"
    with open(path, "w") as f:
        f.write("# Documentation Index\n")
