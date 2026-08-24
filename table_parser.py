import json
import csv
import os
import re
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
import questionary

from ai_analyst import stream_ollama_chat, render_streaming_response, select_or_pull_model

console = Console()

def extract_json_from_response(text: str) -> Optional[Any]:
    """Extract and parse JSON array/object from LLM response."""
    # Look for ```json ... ``` blocks
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    candidate = match.group(1) if match else text

    # Try direct parse
    try:
        return json.loads(candidate.strip())
    except Exception:
        pass

    # Try searching for [ ... ] or { ... }
    bracket_match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', candidate)
    if bracket_match:
        try:
            return json.loads(bracket_match.group(1).strip())
        except Exception:
            pass

    return None

def parse_markdown_table(md_text: str) -> Tuple[List[str], List[List[str]]]:
    """Parse Markdown table into headers and rows."""
    lines = [l.strip() for l in md_text.strip().split('\n') if l.strip().startswith('|') and l.strip().endswith('|')]
    if len(lines) < 2:
        return [], []

    # Header line
    headers = [col.strip() for col in lines[0].strip('|').split('|')]
    # Skip separator line (line 1)
    rows = []
    for line in lines[2:]:
        row = [col.strip() for col in line.strip('|').split('|')]
        # Ensure row length matches headers
        if len(row) < len(headers):
            row.extend([''] * (len(headers) - len(row)))
        elif len(row) > len(headers):
            row = row[:len(headers)]
        rows.append(row)

    return headers, rows

def export_to_csv(headers: List[str], rows: List[List[str]], filepath: str) -> bool:
    """Export tabular data to CSV."""
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if headers:
                writer.writerow(headers)
            writer.writerows(rows)
        return True
    except Exception as e:
        console.print(f"[bold red]❌ CSV Export Error: {e}[/bold red]")
        return False

def export_to_json(data: Any, filepath: str) -> bool:
    """Export structured data to formatted JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        console.print(f"[bold red]❌ JSON Export Error: {e}[/bold red]")
        return False

def interactive_table_parser_session(extracted_text: str, source_name: str = "Extracted Document"):
    """
    Specialized parser for receipts, invoices, tabular data, and lists.
    Extracts structured schema with Ollama LLM and exports to CSV, JSON, or terminal tables.
    """
    if not extracted_text.strip():
        console.print("[bold red]❌ No text available to parse![/bold red]")
        return

    console.print(Panel(
        f"[bold cyan]Document Source:[/bold cyan] [yellow]{source_name}[/yellow]\n"
        "[dim]Automatically converts receipt items, invoices, pricing tables, and spreadsheets into structured CSV / JSON.[/dim]",
        title="[bold magenta]📊 Interactive Table & Receipt Parser[/bold magenta]",
        border_style="magenta"
    ))

    model = select_or_pull_model()
    if not model:
        return

    parser_type = questionary.select(
        "Select Document & Data Type:",
        choices=[
            "🧾 Receipt / Invoice (Extract merchant, date, line items, tax, total)",
            "📋 Generic Table / Spreadsheet (Extract rows, columns & numbers)",
            "🏷️ Key-Value Form / Key Attributes (Extract fields & values into JSON)",
            "⬅️ Back"
        ]
    ).ask()

    if not parser_type or "Back" in parser_type:
        return

    system_prompt = (
        "You are a specialized Data Extraction Engine. Extract tabular or financial information from the OCR text.\n"
        "1. Output a clear Markdown table first.\n"
        "2. Output a valid JSON representation in a ```json ``` block at the end with structured keys."
    )

    if "Receipt / Invoice" in parser_type:
        user_prompt = (
            f"Analyze this receipt/invoice OCR text and extract all details:\n\n{extracted_text}\n\n"
            "Format the line items (Item Name, Quantity, Unit Price, Total Price) into a Markdown Table.\n"
            "Then provide JSON with: merchant_name, date, currency, line_items (list of objects with item, qty, price, total), subtotal, tax, and total_amount."
        )
    elif "Key-Value Form" in parser_type:
        user_prompt = (
            f"Extract all key-value fields and form metadata from this OCR text:\n\n{extracted_text}\n\n"
            "Format into a Markdown Key-Value Table, then output a clean ```json ``` dictionary object."
        )
    else:
        user_prompt = (
            f"Reconstruct any tables, lists, or matrix data found in this OCR text:\n\n{extracted_text}\n\n"
            "Rebuild it as a complete Markdown Table, followed by a ```json ``` array of row objects."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    console.print()
    response = render_streaming_response(model=model, messages=messages, title="Table & Receipt Parser")

    if not response:
        return

    parsed_json = extract_json_from_response(response)
    headers, rows = parse_markdown_table(response)

    # Offer export options
    while True:
        export_choices = []
        if headers and rows:
            export_choices.append("📁 Export Table as CSV (.csv)")
        if parsed_json:
            export_choices.append("📦 Export Structured Data as JSON (.json)")
        export_choices.append("📝 Export Full Markdown Report (.md)")
        export_choices.append("⬅️  Done / Return to Menu")

        exp_action = questionary.select("Export Structured Data:", choices=export_choices).ask()

        if not exp_action or "Return to Menu" in exp_action:
            break

        if "CSV" in exp_action:
            default_csv = f"{source_name.replace(' ', '_').lower()}_table.csv"
            csv_path = questionary.text("Enter CSV filename:", default=default_csv).ask()
            if csv_path:
                if export_to_csv(headers, rows, csv_path):
                    console.print(Panel(
                        f"[bold green]✔ Successfully exported CSV data![/bold green]\n[cyan]{os.path.abspath(csv_path)}[/cyan]\n[dim]Rows: {len(rows)}, Columns: {len(headers)}[/dim]",
                        border_style="green"
                    ))

        elif "JSON" in exp_action:
            default_json = f"{source_name.replace(' ', '_').lower()}_data.json"
            json_path = questionary.text("Enter JSON filename:", default=default_json).ask()
            if json_path:
                if export_to_json(parsed_json, json_path):
                    console.print(Panel(
                        f"[bold green]✔ Successfully exported JSON data![/bold green]\n[cyan]{os.path.abspath(json_path)}[/cyan]",
                        border_style="green"
                    ))

        elif "Markdown" in exp_action:
            default_md = f"{source_name.replace(' ', '_').lower()}_parsed.md"
            md_path = questionary.text("Enter Markdown filename:", default=default_md).ask()
            if md_path:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Structured Document Data: {source_name}\n**Model:** `{model}`\n\n---\n\n{response}\n")
                console.print(Panel(
                    f"[bold green]✔ Successfully exported Markdown report![/bold green]\n[cyan]{os.path.abspath(md_path)}[/cyan]",
                    border_style="green"
                ))

from typing import Tuple
