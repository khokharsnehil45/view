#!/usr/bin/env python3
import os
import sys
import glob
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.align import Align
from rich.text import Text
import questionary

from ocr_engine import OCREngine
from pdf_builder import PDFDocumentBuilder
from navigator import interactive_file_navigator, scan_directory
from ai_analyst import analyze_extracted_text_session, start_interactive_ai_chat, select_or_pull_model
from table_parser import interactive_table_parser_session
from clipboard_handler import get_image_from_clipboard, copy_text_to_clipboard
from updater import run_update

console = Console()

def print_banner():
    banner_ascii = (
        "[bold cyan]"
        "██╗   ██╗██╗███████╗██╗    ██╗\n"
        "██║   ██║██║██╔════╝██║    ██║\n"
        "██║   ██║██║█████╗  ██║ █╗ ██║\n"
        "╚██╗ ██╔╝██║██╔══╝  ██║███╗██║\n"
        " ╚████╔╝ ██║███████╗╚███╔███╔╝\n"
        "  ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝ \n"
        "[/bold cyan]\n"
        "[bold magenta]⚡ The All-in-One Extensible CLI OCR Suite ⚡[/bold magenta]"
    )
    
    banner_panel = Panel(
        Align.left(banner_ascii),
        border_style="bright_cyan",
        padding=(1, 2),
        subtitle="[bold magenta]v1.7.0[/bold magenta] • [bold cyan]Clipboard & Table OCR Engine[/bold cyan]",
        subtitle_align="right"
    )
    console.print(banner_panel)

def display_menu_panel():
    menu_desc = "[bold yellow]🛠️  VIEW Interactive Module Selector[/bold yellow]\n" \
                "[dim]Clipboard OCR, Rapid PP-OCRv4, Visual Navigator, Table/Receipt to CSV, & Ollama AI Chat.[/dim]"
    console.print(Panel(menu_desc, border_style="yellow", padding=(0, 1)))

def get_image_files(paths: List[str]) -> List[str]:
    valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}
    images = []
    for p in paths:
        path_obj = Path(p)
        if path_obj.is_file() and path_obj.suffix.lower() in valid_exts:
            images.append(str(path_obj.resolve()))
        elif path_obj.is_dir():
            for f in path_obj.rglob("*"):
                if f.is_file() and f.suffix.lower() in valid_exts:
                    images.append(str(f.resolve()))
        else:
            for match in glob.glob(p):
                if Path(match).is_file() and Path(match).suffix.lower() in valid_exts:
                    images.append(str(Path(match).resolve()))
    return sorted(list(set(images)))

def run_ocr_and_export(
    image_paths: List[str],
    output_pdf: Optional[str] = None,
    output_txt: Optional[str] = None,
    title: str = "Extracted OCR Document",
    include_thumbnails: bool = True,
    engine_name: str = "rapidocr"
) -> Tuple[bool, List[Dict[str, Any]]]:
    valid_images = [img for img in image_paths if os.path.isfile(img)]
    
    if not valid_images:
        console.print("[bold red]❌ No valid image files found to process![/bold red]")
        return False, []

    console.print(f"\n[bold cyan]🔍 Batch Queue: {len(valid_images)} image(s) to process.[/bold cyan]\n")
    
    table = Table(title="Batch Processing Queue", show_header=True, header_style="bold magenta", border_style="dim")
    table.add_column("#", style="dim", width=4)
    table.add_column("Filename", style="cyan")
    table.add_column("Size", style="green")
    table.add_column("Parent Folder", style="dim")

    for idx, img in enumerate(valid_images, 1):
        try:
            size_kb = f"{os.path.getsize(img) / 1024:.1f} KB"
        except Exception:
            size_kb = "Unknown"
        table.add_row(str(idx), os.path.basename(img), size_kb, os.path.dirname(img))
    console.print(table)
    console.print()

    ocr = OCREngine()
    extracted_data = []

    with Progress(
        SpinnerColumn(style="bold yellow"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=None, style="magenta", complete_style="bold cyan"),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Processing images with OCR...", total=len(valid_images))
        for img in valid_images:
            progress.update(task, description=f"[cyan]Scanning [bold]{os.path.basename(img)}[/bold]...")
            res = ocr.extract(img, prefer=engine_name)
            extracted_data.append(res)
            progress.advance(task)

    console.print("\n[bold green]✔ OCR extraction complete![/bold green]")

    if output_pdf:
        console.print(f"[bold cyan]📄 Compiling structured PDF: [bold yellow]{output_pdf}[/bold yellow]...[/bold cyan]")
        builder = PDFDocumentBuilder(title=title)
        builder.build_pdf(
            extracted_data=extracted_data,
            output_path=output_pdf,
            include_thumbnails=include_thumbnails,
            theme_title=title
        )
        try:
            out_size_kb = f"{os.path.getsize(output_pdf) / 1024:.1f} KB"
        except Exception:
            out_size_kb = "N/A"
        console.print(Panel(
            f"[bold green]✨ Structured PDF Created Successfully![/bold green]\n\n"
            f"[bold white]Output Path:[/bold white] [cyan]{os.path.abspath(output_pdf)}[/cyan]\n"
            f"[bold white]File Size:[/bold white] [green]{out_size_kb}[/green]\n"
            f"[bold white]Batch Pages:[/bold white] [yellow]{len(extracted_data)}[/yellow]",
            border_style="green",
            title="[bold green]PDF Generated[/bold green]"
        ))

    if output_txt:
        combined_text = []
        for d in extracted_data:
            combined_text.append(f"==================================================")
            combined_text.append(f"SOURCE: {os.path.basename(d['image_path'])} (Engine: {d.get('engine', 'OCR')})")
            combined_text.append(f"==================================================")
            combined_text.append(d['full_text'])
            combined_text.append("\n")
        with open(output_txt, 'w', encoding='utf-8') as f:
            f.write("\n".join(combined_text))
        console.print(f"[bold green]✔ Batch text saved to: [cyan]{output_txt}[/cyan][/bold green]")

    for item in extracted_data:
        preview = item['full_text'][:350] + "..." if len(item['full_text']) > 350 else item['full_text']
        console.print(Panel(
            preview if preview.strip() else "[dim italic]No text detected[/dim italic]",
            title=f"[bold green]🔍 {item.get('engine', 'OCR')} Result: {os.path.basename(item['image_path'])}[/bold green]",
            border_style="cyan"
        ))

    return True, extracted_data

def handle_clipboard_ocr(engine_name: str = "rapidocr"):
    """Extract OCR directly from system clipboard image."""
    console.print("\n[bold cyan]📋 Reading image from system clipboard...[/bold cyan]")
    clip_img = get_image_from_clipboard()
    if not clip_img:
        console.print(Panel(
            "[bold red]❌ No image found in clipboard![/bold red]\n\n"
            "[dim]Tip: Copy an image or take a screenshot with PrintScreen / Flameshot / Snip, then run this option.[/dim]",
            border_style="red"
        ))
        return

    success, data = run_ocr_and_export([clip_img], engine_name=engine_name)
    if success and data:
        full_text = data[0]['full_text']
        
        # Action selector for clipboard result
        post_clip = questionary.select(
            "Clipboard OCR Actions:",
            choices=[
                "📋 Copy Extracted Text to Clipboard",
                "💬 Start Continuous AI Chat with this Screenshot",
                "📊 Parse as Table / Receipt to CSV/JSON",
                "📄 Save to Structured PDF",
                "📝 Save to Text File (.txt)",
                "⬅️ Return to Main Menu"
            ]
        ).ask()

        if "Copy Extracted Text" in post_clip:
            copy_text_to_clipboard(full_text, label="OCR Text")
        elif "Start Continuous AI Chat" in post_clip:
            start_interactive_ai_chat(full_text, "Clipboard Screenshot")
        elif "Parse as Table" in post_clip:
            interactive_table_parser_session(full_text, "Clipboard Screenshot")
        elif "Save to Structured PDF" in post_clip:
            pdf_name = questionary.text("Output PDF filename:", default="clipboard_document.pdf").ask()
            if pdf_name:
                PDFDocumentBuilder(title="Clipboard Snapshot OCR").build_pdf(
                    extracted_data=data,
                    output_path=pdf_name,
                    include_thumbnails=True
                )
                console.print(f"[bold green]✔ Saved PDF to: [cyan]{pdf_name}[/cyan][/bold green]")
        elif "Save to Text File" in post_clip:
            txt_name = questionary.text("Output TXT filename:", default="clipboard_text.txt").ask()
            if txt_name:
                with open(txt_name, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                console.print(f"[bold green]✔ Saved TXT to: [cyan]{txt_name}[/cyan][/bold green]")

def run_interactive_mode():
    last_extracted_text = ""
    last_source_label = ""
    default_engine = "rapidocr"

    while True:
        try:
            os.system('clear' if os.name == 'posix' else 'cls')
            print_banner()
            display_menu_panel()

            choices = [
                "📋 Instant Clipboard OCR (Extract text from Copied Screenshot)",
                "📂 Browse Files & Extract OCR (Visual Navigator & PDF/TXT)",
                "📊 Table & Receipt Parser (Extract to CSV / JSON / Markdown)",
                "💬 VIEW AI Chat (Continuous Interactive Chat with Document)",
                "🧠 Local AI Document Analyst (Summary, Takeaways & Structuring)",
                "⚡ Batch OCR Whole Folder / Directory",
                "🖼️  Inspect Directory & List Images",
                f"⚙️  Configure OCR Engine (Current: {default_engine.upper()})",
                "🔄 Check for Updates (Auto-Updater)",
                "------------------------------------",
                "💡 Quick Demo with Screenshot",
                "🚪 Exit VIEW"
            ]

            action = questionary.select(
                "Select a tool to launch: (Use arrow keys)",
                choices=choices,
                use_indicator=True
            ).ask()

            if not action or "Exit VIEW" in action:
                console.print("\n[yellow]Thank you for using VIEW! Goodbye! 👋[/yellow]\n")
                sys.exit(0)

            if "Instant Clipboard OCR" in action:
                handle_clipboard_ocr(engine_name=default_engine)
                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            if "Check for Updates" in action:
                run_update()
                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            if "Table & Receipt Parser" in action:
                ai_sources = []
                if last_extracted_text:
                    ai_sources.append(f"📄 Parse Previous OCR Text ({last_source_label})")
                ai_sources.extend([
                    "📋 Extract from Clipboard Screenshot",
                    "🖼️  Select Images to OCR & Parse (Visual Navigator)",
                    "📁 Choose Existing TXT / Markdown File",
                    "✍️  Paste Raw Text Manually",
                    "⬅️  Back to Main Menu"
                ])
                ai_src = questionary.select("Select Source Document for Table Extraction:", choices=ai_sources).ask()
                
                if not ai_src or "Back to Main Menu" in ai_src:
                    continue

                if "Clipboard Screenshot" in ai_src:
                    clip_img = get_image_from_clipboard()
                    if clip_img:
                        success, data = run_ocr_and_export([clip_img], engine_name=default_engine)
                        if success and data:
                            interactive_table_parser_session(data[0]['full_text'], "Clipboard Screenshot")
                    else:
                        console.print("[red]❌ No image found in clipboard![/red]")
                elif "Previous OCR" in ai_src:
                    interactive_table_parser_session(last_extracted_text, last_source_label)
                elif "Select Images" in ai_src:
                    imgs = interactive_file_navigator()
                    if imgs:
                        success, data = run_ocr_and_export(imgs, engine_name=default_engine)
                        if success and data:
                            combined = "\n\n".join([f"=== {os.path.basename(d['image_path'])} ===\n" + d['full_text'] for d in data])
                            last_extracted_text = combined
                            last_source_label = f"{len(data)} image(s)"
                            interactive_table_parser_session(combined, last_source_label)
                elif "Existing TXT" in ai_src:
                    txt_path = questionary.text("Enter path to text file:").ask()
                    if txt_path and os.path.isfile(txt_path):
                        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        interactive_table_parser_session(content, os.path.basename(txt_path))
                elif "Paste Raw Text" in ai_src:
                    raw_text = questionary.text("Paste text to parse:").ask()
                    if raw_text:
                        interactive_table_parser_session(raw_text, "Manual Input")

                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            elif "Configure OCR Engine" in action:
                cfg_choice = questionary.select(
                    "Select Default OCR Engine:",
                    choices=[
                        "🚀 RapidOCR ONNX (PP-OCRv4 - Ultra-Fast CPU, High Accuracy)",
                        "🐢 EasyOCR (PyTorch Deep Learning Neural Net)",
                        "⚡ Tesseract OCR (Classical Fast)",
                        "⬅️ Back"
                    ]
                ).ask()
                if "RapidOCR" in cfg_choice:
                    default_engine = "rapidocr"
                elif "EasyOCR" in cfg_choice:
                    default_engine = "easyocr"
                elif "Tesseract" in cfg_choice:
                    default_engine = "tesseract"
                
                console.print(f"[bold green]✔ Default engine switched to: {default_engine.upper()}[/bold green]")
                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            elif "VIEW AI Chat" in action:
                ai_sources = []
                if last_extracted_text:
                    ai_sources.append(f"📄 Chat about Previous OCR Text ({last_source_label})")
                ai_sources.extend([
                    "📋 Chat with Clipboard Screenshot",
                    "🖼️  Select Images to OCR & Chat (Visual Navigator)",
                    "📁 Choose Existing TXT / Markdown File",
                    "✍️  Paste Raw Text Manually",
                    "⬅️  Back to Main Menu"
                ])
                ai_src = questionary.select("Select Source Document for AI Chat:", choices=ai_sources).ask()
                
                if not ai_src or "Back to Main Menu" in ai_src:
                    continue

                if "Clipboard Screenshot" in ai_src:
                    clip_img = get_image_from_clipboard()
                    if clip_img:
                        success, data = run_ocr_and_export([clip_img], engine_name=default_engine)
                        if success and data:
                            start_interactive_ai_chat(data[0]['full_text'], "Clipboard Screenshot")
                    else:
                        console.print("[red]❌ No image found in clipboard![/red]")
                elif "Previous OCR" in ai_src:
                    start_interactive_ai_chat(last_extracted_text, last_source_label)
                elif "Select Images" in ai_src:
                    imgs = interactive_file_navigator()
                    if imgs:
                        success, data = run_ocr_and_export(imgs, engine_name=default_engine)
                        if success and data:
                            combined = "\n\n".join([f"=== {os.path.basename(d['image_path'])} ===\n" + d['full_text'] for d in data])
                            last_extracted_text = combined
                            last_source_label = f"{len(data)} image(s)"
                            start_interactive_ai_chat(combined, last_source_label)
                elif "Existing TXT" in ai_src:
                    txt_path = questionary.text("Enter path to text file:").ask()
                    if txt_path and os.path.isfile(txt_path):
                        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        start_interactive_ai_chat(content, os.path.basename(txt_path))
                elif "Paste Raw Text" in ai_src:
                    raw_text = questionary.text("Paste text to chat with:").ask()
                    if raw_text:
                        start_interactive_ai_chat(raw_text, "Manual Input")

                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            elif "Local AI Document Analyst" in action:
                ai_sources = []
                if last_extracted_text:
                    ai_sources.append(f"📄 Use Previously Extracted Text ({last_source_label})")
                ai_sources.extend([
                    "📋 Analyze Clipboard Screenshot",
                    "🖼️  Select Images to OCR & Analyze (Visual Navigator)",
                    "📁 Choose Existing TXT / Markdown File",
                    "✍️  Paste Raw Text Manually",
                    "⬅️  Back to Main Menu"
                ])
                ai_src = questionary.select("Select Source Text for AI Analysis:", choices=ai_sources).ask()
                
                if not ai_src or "Back to Main Menu" in ai_src:
                    continue

                if "Clipboard Screenshot" in ai_src:
                    clip_img = get_image_from_clipboard()
                    if clip_img:
                        success, data = run_ocr_and_export([clip_img], engine_name=default_engine)
                        if success and data:
                            analyze_extracted_text_session(data[0]['full_text'], "Clipboard Screenshot")
                    else:
                        console.print("[red]❌ No image found in clipboard![/red]")
                elif "Previously Extracted" in ai_src:
                    analyze_extracted_text_session(last_extracted_text, last_source_label)
                elif "Select Images" in ai_src:
                    imgs = interactive_file_navigator()
                    if imgs:
                        success, data = run_ocr_and_export(imgs, engine_name=default_engine)
                        if success and data:
                            combined = "\n\n".join([f"=== {os.path.basename(d['image_path'])} ===\n" + d['full_text'] for d in data])
                            last_extracted_text = combined
                            last_source_label = f"{len(data)} image(s)"
                            analyze_extracted_text_session(combined, last_source_label)
                elif "Existing TXT" in ai_src:
                    txt_path = questionary.text("Enter path to text file:").ask()
                    if txt_path and os.path.isfile(txt_path):
                        with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        analyze_extracted_text_session(content, os.path.basename(txt_path))
                elif "Paste Raw Text" in ai_src:
                    raw_text = questionary.text("Paste text to analyze:").ask()
                    if raw_text:
                        analyze_extracted_text_session(raw_text, "Manual Input")
                
                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            elif "Browse Files & Extract OCR" in action:
                selected_images = interactive_file_navigator()
                if not selected_images:
                    console.print("[yellow]No images selected.[/yellow]")
                    questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                    continue

            elif "Batch OCR Whole Folder" in action:
                folder_choices = [
                    "📂 Current Working Directory (.)",
                    "🖼️  Pictures / Screenshots (~/Pictures/Screenshots)",
                    "📁 User Home (~)",
                    "🔍 Visual File Browser...",
                    "⬅️  Back to Main Menu"
                ]
                f_choice = questionary.select("Select directory to batch process:", choices=folder_choices).ask()
                
                if not f_choice or "Back to Main Menu" in f_choice:
                    continue

                if "Current Working" in f_choice:
                    target = "."
                elif "Screenshots" in f_choice:
                    target = str(Path.home() / "Pictures" / "Screenshots")
                elif "User Home" in f_choice:
                    target = str(Path.home())
                else:
                    selected_images = interactive_file_navigator()
                    target = None

                if target:
                    selected_images = get_image_files([target])

            elif "Inspect Directory & List Images" in action:
                selected_images = interactive_file_navigator()
                if selected_images:
                    table = Table(title="Selected Images", show_header=True, header_style="bold magenta")
                    table.add_column("#", width=4)
                    table.add_column("File", style="cyan")
                    table.add_column("Size", style="green")
                    table.add_column("Path", style="dim")
                    for idx, img in enumerate(selected_images, 1):
                        try:
                            size_kb = f"{os.path.getsize(img) / 1024:.1f} KB"
                        except Exception:
                            size_kb = "Unknown"
                        table.add_row(str(idx), os.path.basename(img), size_kb, img)
                    console.print(table)
                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            elif "Quick Demo" in action:
                demo_img = "/home/kevin/Pictures/Screenshots/Screenshot From 2026-08-24 15-24-57.png"
                if os.path.exists(demo_img):
                    success, data = run_ocr_and_export([demo_img], output_pdf="view_demo.pdf", title="VIEW Demo OCR", engine_name=default_engine)
                    if success and data:
                        last_extracted_text = data[0]['full_text']
                        last_source_label = os.path.basename(demo_img)
                else:
                    console.print(f"[yellow]Demo image not found at: {demo_img}[/yellow]")
                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            if not selected_images:
                console.print("[yellow]No images found or selected.[/yellow]")
                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            console.print(f"\n[bold green]✔ Selected {len(selected_images)} image(s) for batch processing.[/bold green]")

            export_format = questionary.select(
                "Select Output Format:",
                choices=[
                    "📄 Structured PDF Document",
                    "📝 Plain Text / Markdown (.txt)",
                    "📦 Both (Structured PDF + TXT)",
                    "🖥️ Terminal Preview Only",
                    "⬅️ Cancel & Return to Main Menu"
                ]
            ).ask()

            if not export_format or "Cancel" in export_format:
                continue

            pdf_out = None
            txt_out = None
            doc_title = "Structured OCR Document"
            inc_thumb = True

            if "PDF" in export_format or "Both" in export_format:
                pdf_out = questionary.text("Output PDF filename:", default="extracted_document.pdf").ask()
                doc_title = questionary.text("Document Title:", default="Extracted Document Summary").ask()
                inc_thumb = questionary.confirm("Include image preview/thumbnails in PDF?", default=True).ask()

            if "Text" in export_format or "Both" in export_format:
                txt_out = questionary.text("Output TXT filename:", default="extracted_text.txt").ask()

            success, data = run_ocr_and_export(
                image_paths=selected_images,
                output_pdf=pdf_out,
                output_txt=txt_out,
                title=doc_title,
                include_thumbnails=inc_thumb,
                engine_name=default_engine
            )

            if success and data:
                combined = "\n\n".join([f"=== {os.path.basename(d['image_path'])} ===\n" + d['full_text'] for d in data])
                last_extracted_text = combined
                last_source_label = f"{len(data)} image(s)"

                post_action = questionary.select(
                    "Next Action with Extracted Text:",
                    choices=[
                        "📋 Copy Extracted Text to Clipboard",
                        "📊 Parse Tables / Receipts to CSV & JSON",
                        "💬 Launch Continuous VIEW AI Chat with this document",
                        "🧠 Run AI Document Analysis (Summary, Tables, Cleaning)",
                        "⬅️ Return to Main Menu"
                    ]
                ).ask()

                if "Copy Extracted Text" in post_action:
                    copy_text_to_clipboard(last_extracted_text, label="Extracted OCR Text")
                elif "Parse Tables" in post_action:
                    interactive_table_parser_session(last_extracted_text, last_source_label)
                elif "VIEW AI Chat" in post_action:
                    start_interactive_ai_chat(last_extracted_text, last_source_label)
                elif "Run AI Document Analysis" in post_action:
                    analyze_extracted_text_session(last_extracted_text, last_source_label)

            questionary.press_any_key_to_continue("\nPress any key to return to main menu...").ask()
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user. Exiting VIEW...[/yellow]")
            sys.exit(0)

@click.group(invoke_without_command=True, context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-i', '--input', 'inputs', multiple=True, help="Input image file(s), folders, or wildcards")
@click.option('-o', '--output', default=None, help="Output PDF filepath (e.g. output.pdf)")
@click.option('--txt', default=None, help="Output TXT filepath (e.g. output.txt)")
@click.option('--csv', 'csv_out', default=None, help="Output CSV filepath for parsed tables/receipts")
@click.option('--json', 'json_out', default=None, help="Output JSON filepath for structured data")
@click.option('-t', '--title', default="Structured OCR Document", help="Document title for the PDF header")
@click.option('--no-thumbnails', is_flag=True, help="Do not include thumbnail images in the generated PDF")
@click.option('--engine', type=click.Choice(['rapidocr', 'easyocr', 'tesseract'], case_sensitive=False), default='rapidocr', help="OCR engine: rapidocr (PP-OCRv4 ONNX), easyocr, tesseract")
@click.option('--clip', is_flag=True, help="Extract OCR directly from image in system clipboard")
@click.option('--copy', 'copy_clip', is_flag=True, help="Copy extracted text directly to clipboard")
@click.option('--analyze', is_flag=True, help="Launch local AI analyst (Ollama) on extracted text after OCR")
@click.option('--chat', is_flag=True, help="Launch interactive multi-turn AI Chat session with document context")
@click.option('--parse-table', is_flag=True, help="Launch table & receipt extraction session")
@click.option('--interactive', '-m', is_flag=True, help="Launch interactive TUI menu & file navigator")
@click.pass_context
def cli(ctx, inputs, output, txt, csv_out, json_out, title, no_thumbnails, engine, clip, copy_clip, analyze, chat, parse_table, interactive):
    """
    \b
    VIEW - High-Precision Document OCR & PDF Structuring Engine
    Extract text from multiple images, clipboard screenshots, tables to CSV/JSON, chat with local LLMs, and compile PDFs.
    """
    if ctx.invoked_subcommand is not None:
        return

    if clip:
        handle_clipboard_ocr(engine_name=engine)
        return

    if interactive or (not inputs and len(sys.argv) == 1):
        run_interactive_mode()
        return

    print_banner()
    
    if not inputs:
        console.print("[bold red]❌ Error: No input images provided.[/bold red] Use [bold yellow]-i <path>[/bold yellow] or run [bold yellow]view --clip[/bold yellow] / [bold yellow]view --interactive[/bold yellow]\n")
        sys.exit(1)

    images = get_image_files(list(inputs))
    if not images:
        console.print(f"[bold red]❌ Error: No valid image files found matching:[/bold red] {inputs}")
        sys.exit(1)

    if not output and not txt and not analyze and not chat and not parse_table and not csv_out and not json_out and not copy_clip:
        output = "output.pdf"

    success, data = run_ocr_and_export(
        image_paths=images,
        output_pdf=output,
        output_txt=txt,
        title=title,
        include_thumbnails=not no_thumbnails,
        engine_name=engine
    )
    if not success:
        sys.exit(1)

    if data:
        combined = "\n\n".join([f"=== {os.path.basename(d['image_path'])} ===\n" + d['full_text'] for d in data])
        if copy_clip:
            copy_text_to_clipboard(combined, label="Extracted OCR Text")
        if chat:
            start_interactive_ai_chat(combined, f"{len(data)} image(s)")
        elif parse_table or csv_out or json_out:
            interactive_table_parser_session(combined, f"{len(data)} image(s)")
        elif analyze:
            analyze_extracted_text_session(combined, f"{len(data)} image(s)")

@cli.command(name="update")
def update_cmd():
    """Check for updates and pull the latest version from GitHub."""
    print_banner()
    run_update()

@cli.command(name="clip")
def clip_cmd():
    """Extract OCR directly from the image stored in your system clipboard."""
    print_banner()
    handle_clipboard_ocr(engine_name="rapidocr")

@cli.command(name="chat")
@click.argument('image_path')
def chat_cmd(image_path):
    """Extract OCR from an image and start continuous AI Chat session immediately."""
    print_banner()
    imgs = get_image_files([image_path])
    if not imgs:
        console.print(f"[bold red]❌ Image not found:[/bold red] {image_path}")
        return
    success, data = run_ocr_and_export(imgs, engine_name="rapidocr")
    if success and data:
        combined = "\n\n".join([f"=== {os.path.basename(d['image_path'])} ===\n" + d['full_text'] for d in data])
        start_interactive_ai_chat(combined, os.path.basename(imgs[0]))

@cli.command(name="parse")
@click.argument('image_path')
def parse_cmd(image_path):
    """Extract OCR from an image and launch Table & Receipt CSV/JSON parser."""
    print_banner()
    imgs = get_image_files([image_path])
    if not imgs:
        console.print(f"[bold red]❌ Image not found:[/bold red] {image_path}")
        return
    success, data = run_ocr_and_export(imgs, engine_name="rapidocr")
    if success and data:
        combined = "\n\n".join([f"=== {os.path.basename(d['image_path'])} ===\n" + d['full_text'] for d in data])
        interactive_table_parser_session(combined, os.path.basename(imgs[0]))

if __name__ == '__main__':
    cli()
