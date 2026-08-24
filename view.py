#!/usr/bin/env python3
import os
import sys
import glob
from pathlib import Path
from typing import List, Optional

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
        subtitle="[bold magenta]v1.1.2[/bold magenta] • [bold cyan]All-in-One CLI Suite[/bold cyan]",
        subtitle_align="right"
    )
    console.print(banner_panel)

def display_menu_panel():
    menu_desc = "[bold yellow]🛠️  VIEW Interactive Module Selector[/bold yellow]\n" \
                "[dim]Browse filesystem visually, extract batch OCR text, and generate structured PDFs.[/dim]"
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
    engine_name: str = "easyocr"
):
    valid_images = [img for img in image_paths if os.path.isfile(img)]
    
    if not valid_images:
        console.print("[bold red]❌ No valid image files found to process![/bold red]")
        return False

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
            combined_text.append(f"SOURCE: {os.path.basename(d['image_path'])}")
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
            title=f"[bold green]🔍 OCR Result: {os.path.basename(item['image_path'])}[/bold green]",
            border_style="cyan"
        ))

    return True

def run_interactive_mode():
    while True:
        try:
            os.system('clear' if os.name == 'posix' else 'cls')
            print_banner()
            display_menu_panel()

            choices = [
                "📂 Browse Files & Extract OCR (Interactive Visual Navigator)",
                "⚡ Batch OCR Whole Folder / Directory",
                "🖼️  Inspect Directory & List Images",
                "⚙️  Configure OCR Engine & Preferences",
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

            selected_images = []

            if "Browse Files & Extract OCR" in action:
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

            elif "Configure OCR Engine" in action:
                cfg_choice = questionary.select(
                    "Select Default Engine:",
                    choices=["EasyOCR (Default - GPU/CPU Neural Net)", "Tesseract OCR (Fast Local)", "⬅️ Back"]
                ).ask()
                if cfg_choice and "Back" not in cfg_choice:
                    console.print(f"[bold green]✔ Engine set to: {cfg_choice}[/bold green]")
                questionary.press_any_key_to_continue("Press any key to return to main menu...").ask()
                continue

            elif "Quick Demo" in action:
                demo_img = "/home/kevin/Pictures/Screenshots/Screenshot From 2026-08-24 15-24-57.png"
                if os.path.exists(demo_img):
                    run_ocr_and_export([demo_img], output_pdf="view_demo.pdf", title="VIEW Demo OCR")
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

            run_ocr_and_export(
                image_paths=selected_images,
                output_pdf=pdf_out,
                output_txt=txt_out,
                title=doc_title,
                include_thumbnails=inc_thumb
            )

            questionary.press_any_key_to_continue("\nPress any key to return to main menu...").ask()
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted by user. Exiting VIEW...[/yellow]")
            sys.exit(0)

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-i', '--input', 'inputs', multiple=True, help="Input image file(s), folders, or wildcards")
@click.option('-o', '--output', default=None, help="Output PDF filepath (e.g. output.pdf)")
@click.option('--txt', default=None, help="Output TXT filepath (e.g. output.txt)")
@click.option('-t', '--title', default="Structured OCR Document", help="Document title for the PDF header")
@click.option('--no-thumbnails', is_flag=True, help="Do not include thumbnail images in the generated PDF")
@click.option('--engine', type=click.Choice(['easyocr', 'tesseract'], case_sensitive=False), default='easyocr', help="OCR engine preference")
@click.option('--interactive', '-m', is_flag=True, help="Launch interactive TUI menu & file navigator")
def cli(inputs, output, txt, title, no_thumbnails, engine, interactive):
    """
    \b
    VIEW - High-Precision Document OCR & PDF Structuring Engine
    Extract text from multiple images and compile them into a clean, structured PDF or TXT.
    """
    if interactive or (not inputs and len(sys.argv) == 1):
        run_interactive_mode()
        return

    print_banner()
    
    if not inputs:
        console.print("[bold red]❌ Error: No input images provided.[/bold red] Use [bold yellow]-i <path>[/bold yellow] or run [bold yellow]view --interactive[/bold yellow]\n")
        sys.exit(1)

    images = get_image_files(list(inputs))
    if not images:
        console.print(f"[bold red]❌ Error: No valid image files found matching:[/bold red] {inputs}")
        sys.exit(1)

    if not output and not txt:
        output = "output.pdf"

    success = run_ocr_and_export(
        image_paths=images,
        output_pdf=output,
        output_txt=txt,
        title=title,
        include_thumbnails=not no_thumbnails,
        engine_name=engine
    )
    if not success:
        sys.exit(1)

if __name__ == '__main__':
    cli()
