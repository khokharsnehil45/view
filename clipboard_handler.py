import io
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image, ImageGrab
import pyperclip
from rich.console import Console
from rich.panel import Panel

console = Console()

def get_image_from_clipboard() -> Optional[str]:
    """
    Grab image directly from system clipboard (supports X11, Wayland, and cross-platform ImageGrab).
    Saves to temporary PNG file and returns the file path.
    """
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, "view_clipboard_image.png")

    # Method 1: Pillow ImageGrab
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            img.save(temp_file, "PNG")
            return temp_file
    except Exception:
        pass

    # Method 2: Wayland (wl-paste)
    try:
        res = subprocess.run(["wl-paste", "--type", "image/png"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0 and res.stdout:
            with open(temp_file, "wb") as f:
                f.write(res.stdout)
            return temp_file
    except Exception:
        pass

    # Method 3: X11 (xclip)
    try:
        res = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if res.returncode == 0 and res.stdout:
            with open(temp_file, "wb") as f:
                f.write(res.stdout)
            return temp_file
    except Exception:
        pass

    return None

def copy_text_to_clipboard(text: str, label: str = "Text") -> bool:
    """Copy given text string to system clipboard with notification."""
    try:
        pyperclip.copy(text)
        console.print(f"[bold green]✔ Copied {label} to clipboard![/bold green]")
        return True
    except Exception as e:
        # Fallback to xclip if pyperclip encounters issues
        try:
            p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            p.communicate(input=text.encode('utf-8'))
            console.print(f"[bold green]✔ Copied {label} to clipboard (via xclip)![/bold green]")
            return True
        except Exception:
            console.print(f"[yellow]⚠️ Could not copy to clipboard: {e}[/yellow]")
            return False
