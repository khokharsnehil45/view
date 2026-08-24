import os
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def get_project_dir() -> Path:
    return Path(__file__).resolve().parent

def run_update() -> bool:
    """Check for updates and pull latest commits from GitHub repository."""
    project_dir = get_project_dir()
    
    console.print(Panel(
        f"[bold cyan]Repository Path:[/bold cyan] [yellow]{project_dir}[/yellow]\n"
        "[bold cyan]Remote URL:[/bold cyan] [green]https://github.com/khokharsnehil45/view[/green]",
        title="[bold magenta]🔄 VIEW Auto-Updater[/bold magenta]",
        border_style="cyan"
    ))

    with Progress(
        SpinnerColumn(style="bold yellow"),
        TextColumn("[bold cyan]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Checking for updates on GitHub...", total=None)

        try:
            # 1. git fetch origin main
            progress.update(task, description="Fetching latest commits from GitHub...")
            fetch_res = subprocess.run(
                ["git", "fetch", "origin", "main"],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if fetch_res.returncode != 0:
                console.print(f"[bold red]❌ Failed to fetch updates: {fetch_res.stderr.strip()}[/bold red]")
                return False

            # 2. Check diff between HEAD and origin/main
            diff_res = subprocess.run(
                ["git", "rev-list", "HEAD..origin/main", "--count"],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            commit_count = diff_res.stdout.strip() if diff_res.returncode == 0 else "0"

            if commit_count == "0":
                progress.stop()
                console.print(Panel(
                    "[bold green]✔ VIEW is already up to date![/bold green]\n"
                    "[dim]No new updates found on remote repository.[/dim]",
                    border_style="green",
                    title="[bold green]Already Latest[/bold green]"
                ))
                return True

            # 3. Pull updates
            progress.update(task, description=f"Applying {commit_count} new update(s)...")
            pull_res = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if pull_res.returncode != 0:
                console.print(f"[bold red]❌ Update failed during git pull: {pull_res.stderr.strip()}[/bold red]")
                return False

            # 4. Update dependencies if requirements.txt exists
            req_file = project_dir / "requirements.txt"
            venv_pip = project_dir / ".venv" / "bin" / "pip"
            if req_file.is_file() and venv_pip.is_file():
                progress.update(task, description="Updating Python dependencies...")
                subprocess.run(
                    [str(venv_pip), "install", "-r", str(req_file), "--upgrade", "--quiet"],
                    cwd=project_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

            progress.stop()
            console.print(Panel(
                f"[bold green]✨ VIEW successfully updated to the latest version![/bold green]\n\n"
                f"[bold white]Updated Commits:[/bold white] [yellow]{commit_count} new commit(s)[/yellow]\n"
                f"[bold white]Status:[/bold white] [green]Ready to use[/green]",
                border_style="green",
                title="[bold green]Update Successful[/bold green]"
            ))
            return True

        except Exception as e:
            progress.stop()
            console.print(f"[bold red]❌ Unexpected error during update: {e}[/bold red]")
            return False
