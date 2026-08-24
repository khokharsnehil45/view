import os
from pathlib import Path
from typing import List, Optional, Tuple
import questionary
from rich.console import Console

console = Console()

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".tif"}

def is_image_file(path: Path) -> bool:
    try:
        return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    except Exception:
        return False

def scan_directory(dir_path: Path) -> Tuple[List[Path], List[Path]]:
    """Returns (subdirectories, image_files) sorted."""
    subdirs = []
    images = []
    try:
        for entry in dir_path.iterdir():
            if entry.name.startswith("."):
                continue
            try:
                if entry.is_dir():
                    subdirs.append(entry)
                elif is_image_file(entry):
                    images.append(entry)
            except Exception:
                continue
    except PermissionError:
        pass

    subdirs.sort(key=lambda x: x.name.lower())
    images.sort(key=lambda x: x.name.lower())
    return subdirs, images

def interactive_file_navigator(start_dir: Optional[str] = None) -> List[str]:
    """
    Interactive terminal file manager / folder browser.
    Allows navigating through folders, selecting single or batch images with checkboxes.
    """
    curr = Path(start_dir).resolve() if start_dir else Path.cwd()
    if not curr.is_dir():
        curr = Path.home()

    while True:
        subdirs, images = scan_directory(curr)

        choices = []

        # Action: Select all images in current folder
        if images:
            choices.append(questionary.Choice(
                title=f"⚡ [SELECT ALL {len(images)} IMAGES IN THIS FOLDER]",
                value="__SELECT_ALL__"
            ))
            choices.append(questionary.Choice(
                title=f"☑️  [CHOOSE MULTIPLE IMAGES WITH CHECKBOXES]",
                value="__MULTI_SELECT__"
            ))

        # Navigation: Go up
        if curr.parent != curr:
            choices.append(questionary.Choice(
                title="📁 .. (Go up to parent directory)",
                value="__PARENT__"
            ))

        # Folder entries
        for d in subdirs:
            img_count = 0
            if d.is_dir() and os.access(d, os.R_OK):
                try:
                    img_count = sum(1 for f in d.iterdir() if is_image_file(f))
                except Exception:
                    pass
            count_str = f" ({img_count} imgs)" if img_count > 0 else ""
            choices.append(questionary.Choice(
                title=f"📁 {d.name}/{count_str}",
                value=f"__DIR__{str(d.resolve())}"
            ))

        # Image entries with exact file path as value
        for img in images:
            try:
                size_kb = f"{img.stat().st_size / 1024:.1f} KB"
            except Exception:
                size_kb = "0 KB"
            choices.append(questionary.Choice(
                title=f"🖼️  {img.name} ({size_kb})",
                value=f"__FILE__{str(img.resolve())}"
            ))

        choices.append(questionary.Choice(
            title="❌ Cancel & Return to Main Menu",
            value="__CANCEL__"
        ))

        console.print(f"\n[bold cyan]📂 Current Directory:[/bold cyan] [bold yellow]{curr}[/bold yellow]")
        if images:
            console.print(f"[dim green]Found {len(images)} image(s) and {len(subdirs)} folder(s)[/dim green]")
        else:
            console.print(f"[dim]{len(subdirs)} folder(s), no images in root of this folder[/dim]")

        selection = questionary.select(
            "Navigate (arrows + Enter) or pick an option:",
            choices=choices,
            use_indicator=True
        ).ask()

        if not selection or selection == "__CANCEL__":
            return []

        if selection == "__SELECT_ALL__":
            return [str(img.resolve()) for img in images if img.is_file()]

        if selection == "__MULTI_SELECT__":
            img_choices = []
            for img in images:
                try:
                    size_kb = f"{img.stat().st_size / 1024:.1f} KB"
                except Exception:
                    size_kb = "0 KB"
                img_choices.append(questionary.Choice(
                    title=f"{img.name} ({size_kb})",
                    value=str(img.resolve()),
                    checked=True
                ))
            selected = questionary.checkbox(
                "Select images to include (Space to toggle, Enter to confirm):",
                choices=img_choices
            ).ask()
            if selected:
                return [p for p in selected if os.path.isfile(p)]
            continue

        if selection == "__PARENT__":
            curr = curr.parent
            continue

        if selection.startswith("__DIR__"):
            next_dir = Path(selection.replace("__DIR__", ""))
            if next_dir.is_dir():
                curr = next_dir
            continue

        if selection.startswith("__FILE__"):
            file_path = selection.replace("__FILE__", "")
            if os.path.isfile(file_path):
                return [file_path]
            continue
