import json
import os
import subprocess
import urllib.request
import urllib.error
from typing import List, Optional, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
import questionary

console = Console()

OLLAMA_API_BASE = "http://127.0.0.1:11434"

def get_installed_ollama_models() -> List[str]:
    """Retrieve list of locally downloaded Ollama models."""
    try:
        req = urllib.request.Request(f"{OLLAMA_API_BASE}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            return models
    except Exception:
        # Fallback to CLI command
        try:
            res = subprocess.run(["ollama", "list"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                lines = res.stdout.strip().split("\n")
                if len(lines) > 1:
                    models = []
                    for line in lines[1:]:
                        parts = line.split()
                        if parts:
                            models.append(parts[0])
                    return models
        except Exception:
            pass
    return []

def pull_ollama_model(model_name: str) -> bool:
    """Pull / download a new model using Ollama CLI with live display."""
    console.print(f"\n[bold cyan]📥 Pulling model: [bold yellow]{model_name}[/bold yellow] via Ollama...[/bold cyan]")
    try:
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in iter(process.stdout.readline, ''):
            if line:
                console.print(f"[dim cyan]{line.strip()}[/dim cyan]")
        process.stdout.close()
        process.wait()
        return process.returncode == 0
    except Exception as e:
        console.print(f"[bold red]❌ Failed to pull model {model_name}: {e}[/bold red]")
        return False

def select_or_pull_model() -> Optional[str]:
    """Interactively select an installed model or download a new one."""
    installed = get_installed_ollama_models()
    
    choices = []
    if installed:
        choices.append(questionary.Separator("── Local Downloaded Models ──"))
        for m in installed:
            choices.append(questionary.Choice(title=f"🧠 {m} (Ready)", value=m))
            
    choices.append(questionary.Separator("── Download New Model ──"))
    choices.append(questionary.Choice(title="⬇️  Download Popular Model (llama3.2, mistral, deepseek-r1, qwen2.5)...", value="__POPULAR__"))
    choices.append(questionary.Choice(title="✍️  Enter Custom Model Name to Pull...", value="__CUSTOM__"))
    choices.append(questionary.Separator("────────────────────────────"))
    choices.append(questionary.Choice(title="⬅️  Back to Menu", value="__BACK__"))

    selected = questionary.select(
        "Select Local Ollama LLM Model to Use:",
        choices=choices,
        use_indicator=True
    ).ask()

    if not selected or selected == "__BACK__":
        return None

    if selected == "__POPULAR__":
        popular_models = [
            "llama3.2:3b (Fast & Lightweight - 2GB)",
            "llama3.2:1b (Ultra Fast - 1.3GB)",
            "llama3.1:8b (High Intelligence - 4.7GB)",
            "mistral:7b (Great for Analysis - 4.1GB)",
            "deepseek-r1:7b (Reasoning & Math - 4.7GB)",
            "deepseek-r1:1.5b (Fast Reasoning - 1.1GB)",
            "qwen2.5:3b (High Multilingual Precision - 1.9GB)",
            "phi3:mini (Compact High Quality - 2.2GB)",
            "⬅️ Back"
        ]
        choice = questionary.select("Choose model to download:", choices=popular_models).ask()
        if not choice or "Back" in choice:
            return select_or_pull_model()
        
        model_name = choice.split()[0].strip()
        success = pull_ollama_model(model_name)
        if success:
            console.print(f"[bold green]✔ Successfully downloaded {model_name}![/bold green]")
            return model_name
        else:
            return None

    if selected == "__CUSTOM__":
        custom_name = questionary.text("Enter model name (e.g. llama3:8b, mistral, gemma2:2b):").ask()
        if not custom_name:
            return None
        success = pull_ollama_model(custom_name.strip())
        if success:
            console.print(f"[bold green]✔ Successfully downloaded {custom_name}![/bold green]")
            return custom_name.strip()
        else:
            return None

    return selected

def query_ollama(model: str, system_prompt: str, user_prompt: str) -> Optional[str]:
    """Send prompt to local Ollama API."""
    url = f"{OLLAMA_API_BASE}/api/generate"
    payload = {
        "model": model,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            res_json = json.loads(resp.read().decode('utf-8'))
            return res_json.get("response", "")
    except urllib.error.URLError as e:
        console.print(f"[bold red]❌ Failed to connect to Ollama ({e}). Make sure 'ollama serve' or Ollama daemon is running.[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]❌ Error during Ollama inference: {e}[/bold red]")
        return None

def analyze_extracted_text_session(extracted_text: str, source_name: str = "Extracted Document"):
    """Interactive AI Analyst session for extracted OCR text."""
    if not extracted_text.strip():
        console.print("[bold red]❌ No text available to analyze![/bold red]")
        return

    console.print(Panel(
        f"[bold cyan]Document Source:[/bold cyan] [yellow]{source_name}[/yellow]\n"
        f"[bold cyan]Character Count:[/bold cyan] [green]{len(extracted_text)} chars[/green]",
        title="[bold magenta]🧠 Local AI Document Analyst (Ollama)[/bold magenta]",
        border_style="magenta"
    ))

    model = select_or_pull_model()
    if not model:
        return

    console.print(f"\n[bold green]✔ Active Model: [bold cyan]{model}[/bold cyan][/bold green]\n")

    system_prompt = (
        "You are an expert AI Document Analyst. You analyze text extracted from OCR images and scans. "
        "Provide clear, structured, well-formatted answers in GitHub-style Markdown."
    )

    while True:
        task_choices = [
            "📋 Comprehensive Document Summary",
            "🔑 Key Takeaways & Action Items Extractor",
            "📊 Structured Data / Table Reconstructor (Markdown format)",
            "🧹 Clean Up OCR Typos & Fix Grammar",
            "❓ Ask Custom Question / Freeform Chat about this Text",
            "💾 Export Analysis to Markdown / TXT",
            "⬅️  Return to Main Menu"
        ]

        action = questionary.select(
            "Select Analysis Task:",
            choices=task_choices,
            use_indicator=True
        ).ask()

        if not action or "Return to Main Menu" in action:
            break

        user_prompt = ""
        task_title = ""

        if "Comprehensive Document Summary" in action:
            task_title = "Document Summary"
            user_prompt = f"Please provide an executive summary and detailed section-by-section breakdown of this OCR document:\n\n{extracted_text}"

        elif "Key Takeaways" in action:
            task_title = "Key Takeaways & Actions"
            user_prompt = f"Extract the key takeaways, bulleted insights, decisions, and any action items found in this text:\n\n{extracted_text}"

        elif "Structured Data" in action:
            task_title = "Structured Data & Tables"
            user_prompt = f"Organize the extracted text into neat markdown tables, bullet hierarchies, and structured key-value pairs where applicable:\n\n{extracted_text}"

        elif "Clean Up OCR Typos" in action:
            task_title = "Cleaned & Corrected Text"
            user_prompt = f"Proofread and reconstruct this raw OCR text. Fix OCR spelling glitches, broken words, line wraps, and formatting while preserving original meaning:\n\n{extracted_text}"

        elif "Ask Custom Question" in action:
            custom_q = questionary.text("Enter your question or prompt about this document:").ask()
            if not custom_q:
                continue
            task_title = f"Q&A: {custom_q[:40]}"
            user_prompt = f"Based on the following document context:\n\n{extracted_text}\n\nAnswer this question: {custom_q}"

        if user_prompt:
            with Progress(
                SpinnerColumn(style="bold magenta"),
                TextColumn("[bold cyan]Analyzing with {task.fields[model]}..."),
                console=console
            ) as progress:
                t = progress.add_task("analyst", total=None, model=model)
                response = query_ollama(model=model, system_prompt=system_prompt, user_prompt=user_prompt)

            if response:
                console.print()
                console.print(Panel(
                    Markdown(response),
                    title=f"[bold green]✨ AI Analysis: {task_title} ({model})[/bold green]",
                    border_style="cyan",
                    padding=(1, 2)
                ))

                save_opt = questionary.confirm("Save this AI analysis to a file?", default=False).ask()
                if save_opt:
                    filename = questionary.text("Enter filename:", default=f"analysis_{task_title.replace(' ', '_').lower()}.md").ask()
                    if filename:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"# AI Analysis: {task_title}\n\n**Model:** `{model}`\n**Source:** `{source_name}`\n\n---\n\n{response}\n")
                        console.print(f"[bold green]✔ Saved analysis to: [cyan]{filename}[/cyan][/bold green]")

        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
