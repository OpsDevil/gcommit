"""
CLI interface for AI-powered git commit message generator.
"""

import os
import subprocess
import sys
import tempfile
from typing import Optional

import typer

from .git_ops import get_git_changes, make_commit
from .llm import generate_commit_message, load_config


app = typer.Typer(help='AI-powered git commit message generator')


def edit_in_editor(message: str) -> Optional[str]:
    """Open editor to edit commit message"""
    # TODO: add support for other env, gitconfig, etc.
    editor = os.getenv('EDITOR', 'vim')

    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        f.write(message)
        tmp_path = f.name
    try:
        subprocess.run([editor, tmp_path], check=False)
        with open(tmp_path, 'r', encoding='utf-8') as f:
            edited = f.read().strip()
        return edited or None
    finally:
        try:
            os.remove(tmp_path)
        except FileNotFoundError:
            pass


def interactive_confirm(message: str) -> Optional[str]:
    """Ask user to confirm or edit commit message."""
    choice = input('\n[y]es / [n]o / [e]dit: ').strip().lower()

    if choice in ['y', 'yes']:
        return message

    if choice in ['n', 'no']:
        typer.secho('Commit cancelled', fg=typer.colors.RED)
        return None

    if choice in ['e', 'edit']:
        typer.echo('Opening editor...')
        edited = edit_in_editor(message)
        if edited:
            return edited
        typer.secho('Commit cancelled (empty message)', fg=typer.colors.RED)
        return None

    typer.secho('Invalid choice. Commit cancelled', fg=typer.colors.RED)
    return None


@app.command()
def main(
    auto: bool = typer.Option(False, '--auto', help='Auto-commit without confirmation'),
    commit_format: Optional[str] = typer.Option(None, '--format', help='Commit format (conventional or simple)'),
    edit: bool = typer.Option(False, '--edit', help='Open editor to edit generated message'),
    language: Optional[str] = typer.Option(None, '--language', help='Commit message language (e.g., english, russian)'),
    message: Optional[str] = typer.Option(None, '-m', '--message', help='User hint for commit message'),
    model: Optional[str] = typer.Option(None, '--model', help='LLM model to use (e.g., gpt-4o-mini)'),
    verbose: bool = typer.Option(False, '--verbose', help='Show detailed information'),
):
    """Generate and commit with AI-generated message"""
    if auto and edit:
        typer.secho('Options --auto and --edit are mutually exclusive.', fg=typer.colors.RED)
        sys.exit(1)

    try:
        config = load_config(model=model, language=language, commit_format=commit_format)
    except SystemExit:
        return
    except Exception as e:
        typer.secho(f'Error loading config: {e}', fg=typer.colors.RED)
        sys.exit(1)

    typer.echo('Analyzing changes...')
    changes = get_git_changes()
    if verbose:
        typer.echo(f'[DEBUG] Found {len(changes.staged_files)} staged files')
        typer.echo(f'[DEBUG] Diff: {len(changes.diff)} characters')

    generated_message = generate_commit_message(
        changes.staged_files, changes.diff, config, user_hint=message, verbose=verbose
    )
    if not generated_message.strip():
        typer.secho('Generated empty message.', fg=typer.colors.RED)
        sys.exit(1)
    typer.echo(f'\nProposed commit message:\n{generated_message}\n')

    final_message: Optional[str] = None
    if auto:
        final_message = generated_message
    elif edit:
        edited_message = edit_in_editor(generated_message)
        if not edited_message:
            typer.secho('Commit cancelled (empty message).', fg=typer.colors.RED)
            sys.exit(1)
        final_message = edited_message
    else:
        final_message = interactive_confirm(generated_message)
        if not final_message:
            typer.secho('Commit cancelled (empty message).', fg=typer.colors.RED)
            sys.exit(1)

    make_commit(final_message)

    typer.secho('Committed successfully', fg=typer.colors.GREEN)


if __name__ == '__main__':
    app()
