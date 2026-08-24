import json
import os
import subprocess
import urllib.request
import urllib.error
from typing import List, Optional, Dict, Any, Generator

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
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

def stream_ollama_chat(model: str, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
    """Stream token chunks from local Ollama chat API."""
    url = f"{OLLAMA_API_BASE}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": True
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=180) as resp:
            for line in resp:
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    except urllib.error.URLError as e:
        console.print(f"[bold red]❌ Failed to connect to Ollama ({e}). Make sure Ollama is running.[/bold red]")
        return
    except Exception as e:
        console.print(f"[bold red]❌ Error during Ollama streaming: {e}[/bold red]")
        return

def render_streaming_response(model: str, messages: List[Dict[str, str]], title: str = "VIEW AI") -> str:
    """Renders token-by-token live markdown response inside a rich Panel."""
    full_response = []
    
    with Live(
        Panel(
            "[dim italic]Thinking and generating tokens...[/dim italic]",
            title=f"[bold cyan]🤖 {title} ({model})[/bold cyan]",
            border_style="bright_cyan",
            padding=(1, 2)
        ),
        console=console,
        refresh_per_second=15
    ) as live:
        for chunk in stream_ollama_chat(model=model, messages=messages):
            full_response.append(chunk)
            current_text = "".join(full_response)
            live.update(Panel(
                Markdown(current_text),
                title=f"[bold cyan]🤖 {title} ({model})[/bold cyan]",
                border_style="bright_cyan",
                padding=(1, 2)
            ))
            
    return "".join(full_response)

def start_interactive_ai_chat(extracted_text: str, source_name: str = "Extracted Document", model: Optional[str] = None):
    """Continuous multi-turn conversational REPL with real-time streaming tokens."""
    if not model:
        model = select_or_pull_model()
        if not model:
            return

    console.print(Panel(
        f"[bold cyan]Document Context:[/bold cyan] [yellow]{source_name}[/yellow] ([green]{len(extracted_text)} chars[/green])\n"
        f"[bold cyan]Model:[/bold cyan] [magenta]{model}[/magenta] • [bold green]⚡ Live Token Streaming Enabled[/bold green]\n\n"
        "[dim]Commands: Type your question, or enter [bold yellow]/save[/bold yellow] (export chat), [bold yellow]/clear[/bold yellow] (reset chat), or [bold red]/exit[/bold red] (quit chat).[/dim]",
        title="[bold magenta]💬 VIEW AI Document Chat (Interactive REPL)[/bold magenta]",
        border_style="magenta"
    ))

    system_content = (
        "You are an expert AI Document Intelligence assistant. You are conversing with the user about a document "
        "whose text was extracted via OCR. Answer questions accurately and concisely based on this document context.\n\n"
        f"--- START OF DOCUMENT CONTEXT ({source_name}) ---\n"
        f"{extracted_text}\n"
        "--- END OF DOCUMENT CONTEXT ---"
    )

    messages = [
        {"role": "system", "content": system_content}
    ]

    session = PromptSession(history=InMemoryHistory())

    while True:
        try:
            user_input = session.prompt("\n💬 Ask VIEW AI > ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("/exit", "/quit", "exit", "quit", ":q"):
                console.print("[yellow]Ending AI Chat session...[/yellow]")
                break

            if user_input.lower() == "/clear":
                messages = [{"role": "system", "content": system_content}]
                console.print("[bold yellow]🧹 Chat history cleared![/bold yellow]")
                continue

            if user_input.lower() == "/save":
                export_fn = f"chat_history_{source_name.replace(' ', '_').lower()}.md"
                with open(export_fn, 'w', encoding='utf-8') as f:
                    f.write(f"# VIEW AI Chat History: {source_name}\n**Model:** `{model}`\n\n---\n\n")
                    for m in messages:
                        if m['role'] == 'user':
                            f.write(f"### 👤 User:\n{m['content']}\n\n")
                        elif m['role'] == 'assistant':
                            f.write(f"### 🤖 VIEW AI ({model}):\n{m['content']}\n\n---\n\n")
                console.print(f"[bold green]✔ Chat history exported to: [cyan]{export_fn}[/cyan][/bold green]")
                continue

            messages.append({"role": "user", "content": user_input})
            console.print()

            assistant_reply = render_streaming_response(model=model, messages=messages, title=f"VIEW AI")

            if assistant_reply:
                messages.append({"role": "assistant", "content": assistant_reply})
            else:
                messages.pop()

        except KeyboardInterrupt:
            console.print("\n[yellow]Chat cancelled by user.[/yellow]")
            break
        except EOFError:
            break

def analyze_extracted_text_session(extracted_text: str, source_name: str = "Extracted Document"):
    """Interactive AI Analyst session for extracted OCR text with live streaming."""
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

    console.print(f"\n[bold green]✔ Active Model: [bold cyan]{model}[/bold cyan] • [bold green]⚡ Streaming Active[/bold green][/bold green]\n")

    while True:
        task_choices = [
            "💬 Start Continuous Multi-Turn AI Chat (REPL)",
            "📋 Comprehensive Document Summary",
            "🔑 Key Takeaways & Action Items Extractor",
            "📊 Structured Data / Table Reconstructor (Markdown format)",
            "🧹 Clean Up OCR Typos & Fix Grammar",
            "❓ Single Question / Quick Query",
            "⬅️  Return to Main Menu"
        ]

        action = questionary.select(
            "Select Analysis Task:",
            choices=task_choices,
            use_indicator=True
        ).ask()

        if not action or "Return to Main Menu" in action:
            break

        if "Start Continuous Multi-Turn AI Chat" in action:
            start_interactive_ai_chat(extracted_text, source_name, model=model)
            continue

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

        elif "Single Question" in action:
            custom_q = questionary.text("Enter your question about this document:").ask()
            if not custom_q:
                continue
            task_title = f"Q&A: {custom_q[:40]}"
            user_prompt = f"Based on the following document context:\n\n{extracted_text}\n\nAnswer this question: {custom_q}"

        if user_prompt:
            system_prompt = (
                "You are an expert AI Document Analyst. You analyze text extracted from OCR images and scans. "
                "Provide clear, structured, well-formatted answers in GitHub-style Markdown."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            console.print()
            response = render_streaming_response(model=model, messages=messages, title=f"AI Analysis: {task_title}")

            if response:
                save_opt = questionary.confirm("Save this AI analysis to a file?", default=False).ask()
                if save_opt:
                    filename = questionary.text("Enter filename:", default=f"analysis_{task_title.replace(' ', '_').lower()}.md").ask()
                    if filename:
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"# AI Analysis: {task_title}\n\n**Model:** `{model}`\n**Source:** `{source_name}`\n\n---\n\n{response}\n")
                        console.print(f"[bold green]✔ Saved analysis to: [cyan]{filename}[/cyan][/bold green]")

        questionary.press_any_key_to_continue("\nPress any key to continue...").ask()
