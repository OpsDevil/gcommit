"""Git operations module"""

import subprocess
import sys
from dataclasses import dataclass
from typing import List

import typer


@dataclass
class GitChanges:
    """Git changes information"""
    staged_files: List[str]
    diff: str


def check_git_repo() -> bool:
    """Check if current directory is a git repository"""
    try:
        result = subprocess.run(["git", "rev-parse", "--git-dir"], capture_output=True, text=True, check=False)
        return result.returncode == 0
    except Exception as e:
        typer.secho(f"Error checking git repository: {e}", fg=typer.colors.RED)
        return False


def get_staged_files() -> List[str]:
    """Get list of staged files"""
    try:
        result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True)
        files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
        return files
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error getting staged files: {e}", fg=typer.colors.RED)
        sys.exit(1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        sys.exit(1)


def get_diff() -> str:
    """Get git diff for staged changes"""
    try:
        result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error getting diff: {e}", fg=typer.colors.RED)
        sys.exit(1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        sys.exit(1)


def get_git_changes() -> GitChanges:
    """Get all git changes (staged files + diff)"""
    if not check_git_repo():
        typer.secho("Not a git repository", fg=typer.colors.RED)
        sys.exit(1)

    staged_files = get_staged_files()
    if not staged_files:
        typer.secho("No staged files found. Use 'git add' first.", fg=typer.colors.RED)
        sys.exit(1)

    diff = get_diff()
    return GitChanges(staged_files=staged_files, diff=diff)


def make_commit(message: str) -> None:
    """Make git commit with given message"""
    try:
        subprocess.run(["git", "commit", "-m", message], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        typer.secho(f"Error making commit: {e}", fg=typer.colors.RED)
        sys.exit(1)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        sys.exit(1)
