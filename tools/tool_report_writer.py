from typing import Dict, Any
from tools.base import BaseTool
from core.state_manager import StateManager
import markdown
from datetime import datetime


class ReportWriterTool(BaseTool):
    """Tool to compile markdown text into a professionally styled HTML report."""

    @classmethod
    def get_name(cls) -> str:
        return "tool_report_writer"

    @classmethod
    def get_description(cls) -> str:
        return (
            "TOOL NAME: tool_report_writer\n"
            "DESCRIPTION: Takes raw markdown text and writes it to a professionally styled local HTML file. ALWAYS use this tool first to create a PDF report.\n"
            "REQUIRED ARGS:\n"
            "  - content (str): Markdown formatted text\n"
            "  - output_path (str): Absolute local file path ending in .html\n"
            "OPTIONAL ARGS:\n"
            "  - title (str): Report title for the header section (default: 'Report')\n"
            "STATE OUTPUT: None. (Pass EXACT 'output_path' to tool_pdf_generator 'url' next)"
        )

    def _get_stylesheet(self) -> str:
        """Generate a formal, professional CSS stylesheet — monochrome, minimal, business-grade."""
        return """

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Georgia, 'Times New Roman', serif;
            background: #ffffff;
            color: #1a1a1a;
            line-height: 1.85;
            font-size: 14.5px;
            -webkit-font-smoothing: antialiased;
        }

        .report-container {
            padding: 0 0 40px;
        }

        /* ── Header Section ─────────────────────────── */
        .cover {
            background: #ffffff;
            color: #1a1a1a;
            padding: 0 0 20px;
            margin-bottom: 28px;
            border-bottom: 2px solid #1a1a1a;
        }

        .cover h1 {
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 2.2em;
            font-weight: 700;
            letter-spacing: -0.5px;
            margin-bottom: 6px;
            color: #1a1a1a;
            line-height: 1.2;
        }

        .cover .meta {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 0.82em;
            color: #777777;
            font-weight: 400;
            letter-spacing: 0.2px;
            margin-top: 4px;
        }

        .cover .divider {
            display: none;
        }

        /* ── Headings ───────────────────────────────── */
        h1, h2, h3, h4, h5, h6 {
            font-family: Georgia, 'Times New Roman', serif;
            color: #1a1a1a;
            font-weight: 600;
            letter-spacing: -0.2px;
            margin-top: 2em;
            margin-bottom: 0.5em;
        }

        h1 {
            font-size: 1.75em;
            padding-bottom: 8px;
            border-bottom: 1px solid #dddddd;
        }

        h2 {
            font-size: 1.4em;
            padding-bottom: 6px;
            border-bottom: 1px solid #e8e8e8;
        }

        h3 {
            font-size: 1.15em;
            color: #333333;
        }

        h4 {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 0.9em;
            color: #555555;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            font-weight: 600;
        }

        /* ── Paragraphs & Text ──────────────────────── */
        p {
            margin-bottom: 1.1em;
            color: #2a2a2a;
            text-align: justify;
        }

        strong {
            font-weight: 700;
            color: #1a1a1a;
        }

        em {
            font-style: italic;
        }

        a {
            color: #333333;
            text-decoration: underline;
            text-underline-offset: 2px;
        }

        /* ── Tables ─────────────────────────────────── */
        table {
            width: 100%;
            table-layout: fixed;
            border-collapse: collapse;
            margin: 1.5em 0;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 0.82em;
            line-height: 1.5;
        }

        thead tr {
            background: #f5f5f5;
            border-bottom: 2px solid #cccccc;
        }

        th {
            padding: 8px 10px;
            text-align: left;
            font-weight: 600;
            font-size: 0.78em;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            color: #333333;
        }

        td {
            padding: 7px 10px;
            border-bottom: 1px solid #e5e5e5;
            color: #2a2a2a;
            vertical-align: top;
            word-break: break-word;
            overflow-wrap: break-word;
            font-size: 0.8em;
        }

        tbody tr {
            background: #ffffff;
        }

        tbody tr:nth-child(even) {
            background: #fafafa;
        }

        tbody tr:last-child td {
            border-bottom: none;
        }

        /* ── Code Blocks ────────────────────────────── */
        pre {
            background: #f7f7f7;
            border: 1px solid #e0e0e0;
            border-radius: 3px;
            padding: 16px 20px;
            overflow-x: auto;
            margin: 1.5em 0;
            font-size: 0.85em;
            line-height: 1.65;
        }

        pre code {
            font-family: 'Consolas', 'Courier New', monospace;
            color: #1a1a1a;
            background: none;
            padding: 0;
            border: none;
            font-size: inherit;
        }

        code {
            font-family: 'Consolas', 'Courier New', monospace;
            background: #f3f3f3;
            color: #333333;
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 0.85em;
            border: 1px solid #e5e5e5;
        }

        /* ── Blockquotes ────────────────────────────── */
        blockquote {
            border-left: 3px solid #cccccc;
            background: #fafafa;
            padding: 14px 22px;
            margin: 1.5em 0;
            color: #555555;
            font-style: italic;
        }

        blockquote p {
            margin-bottom: 0;
        }

        /* ── Lists ──────────────────────────────────── */
        ul, ol {
            margin: 1em 0;
            padding-left: 24px;
        }

        li {
            margin-bottom: 0.4em;
            line-height: 1.7;
            color: #2a2a2a;
        }

        /* ── Horizontal Rules ───────────────────────── */
        hr {
            border: none;
            height: 1px;
            background: #dddddd;
            margin: 2.5em 0;
        }

        /* ── Images ─────────────────────────────────── */
        img {
            max-width: 100%;
            height: auto;
            margin: 1.5em 0;
            border: 1px solid #e5e5e5;
        }

        /* ── Footer ─────────────────────────────────── */
        .footer {
            margin-top: 48px;
            padding-top: 16px;
            border-top: 1px solid #dddddd;
            text-align: center;
            font-family: Arial, Helvetica, sans-serif;
            color: #999999;
            font-size: 0.78em;
            letter-spacing: 0.2px;
        }

        /* ── Print / PDF Rules ──────────────────────── */
        @media print {
            body { font-size: 12.5px; }
            h1, h2, h3 { page-break-after: avoid; }
            pre { page-break-inside: avoid; }
            .footer { page-break-before: avoid; }
        }
        """

    def run(self, state: StateManager, args: Dict[str, Any]) -> bool:
        content = args.get("content")
        output_path = args.get("output_path")
        title = args.get("title", "Report")

        if not content or not output_path:
            print("\033[38;5;196m[ ERROR ]\033[0m tool_report_writer requires 'content' and 'output_path'.")
            return False

        print(f"\033[38;5;39m[ REPORT WRITER ]\033[0m Compiling professional report to {output_path}...")

        try:
            # Parse markdown with extensions for tables, code, etc.
            extensions = ["tables", "fenced_code", "nl2br", "sane_lists"]
            try:
                html_content = markdown.markdown(content, extensions=extensions)
            except Exception:
                try:
                    html_content = markdown.markdown(content, extensions=["tables", "fenced_code"])
                except Exception:
                    html_content = markdown.markdown(content)

            # Generate date string
            date_str = datetime.now().strftime("%B %d, %Y")

            # Build the full HTML
            stylesheet = self._get_stylesheet()

            full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{stylesheet}</style>
</head>
<body>
    <div class="report-container">
        <div class="cover">
            <h1>{title}</h1>
            <div class="meta">{date_str}</div>
            <div class="meta">ORBIT</div>
        </div>
        {html_content}
        <div class="footer">
            Generated by ORBIT &nbsp;&bull;&nbsp; {date_str}
        </div>
    </div>
</body>
</html>"""

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_html)

            print(f"\033[38;5;114m[ SUCCESS ]\033[0m Professional report generated at {output_path}")
            return True
        except Exception as e:
            print(f"\033[38;5;196m[ ERROR ]\033[0m Report generation failed: {e}")
            return False
