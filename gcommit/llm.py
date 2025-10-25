"""LLM integration module"""

import time
from typing import List, Optional

import typer
from openai import OpenAI

from gcommit.config import Config, load_config


def build_prompt(staged_files: List[str], diff: str, config: Config, user_hint: Optional[str] = None) -> str:
    """Build prompt for LLM"""
    files_list = ', '.join(staged_files)

    # Format-specific instructions
    format_instructions = {
        'conventional': """
Follow Conventional Commits specification (https://www.conventionalcommits.org/):

Format: <type>: <subject>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style/formatting (no logic change)
- refactor: Code refactoring
- test: Adding/updating tests
- chore: Build/tooling changes
- perf: Performance improvements

Rules:
- Use lowercase for type
- Subject in imperative mood ("add" not "added")
- No period at end of subject
- Subject max 72 chars
- Body max 72 chars per line (if needed)
- Separate subject and body with blank line
- Output exactly ONE commit message

Example:
feat: add JWT authentication

Implement JWT-based authentication with refresh tokens.
Add middleware for protected routes.
""",
        'simple': """
Write a simple, clear commit message in imperative mood.

Rules:
- Start with a verb ("add", "fix", "update", etc.)
- No period at end
- Max 72 chars total
- Single line only, no body
- Be concise and descriptive
- Output exactly ONE commit message

Examples:
add user authentication
fix login validation bug
update dependencies to latest versions
""",
    }

    if config.commit_format == 'custom':
        if config.custom_template:
            format_instructions['custom'] = f"""
Use the following custom template for commit message:

{config.custom_template}

Follow the template structure and fill with appropriate content based on the changes.
"""
        else:
            typer.secho("Error: custom_template not configured for 'custom' format", fg=typer.colors.RED)
            exit(1)

    instructions = format_instructions.get(config.commit_format, format_instructions['conventional'])

    prompt = f"""You are a Git commit message generator.
Analyze the git diff and generate a commit message.

Language: {config.language}
{instructions}
"""

    if user_hint:
        prompt += f"""User context: {user_hint}
(Use this as additional context to understand the changes better)

"""

    prompt += f"""Staged files: {files_list}

Git diff:
{diff}

Generate a commit message following the rules above."""

    return prompt


def clean_markdown_code_blocks(text: str) -> str:
    """Remove markdown code blocks from text"""
    text = text.strip()

    # Remove code blocks with language identifier: ```python\n...\n```
    if text.startswith('```') and text.endswith('```'):
        lines = text.split('\n')
        # Remove first and last lines (``` markers)
        text = '\n'.join(lines[1:-1])

    return text.strip()


def generate_commit_message(
    staged_files: List[str], diff: str, config: Config, user_hint: Optional[str] = None, verbose: bool = False
) -> str:
    """Generate commit message using OpenAI API"""
    prompt = build_prompt(staged_files, diff, config, user_hint)
    if verbose:
        typer.echo('[DEBUG] Prompt:')
        typer.echo('=' * 80)
        typer.echo(prompt)
        typer.echo('=' * 80)
        typer.echo(f'[DEBUG] Calling OpenAI API (model: {config.model}, temp: {config.temperature})')
    try:
        start = time.time()
        client = OpenAI(api_key=config.openai_api_key, base_url=config.base_url)
        response = client.chat.completions.create(
            model=config.model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        elapsed = time.time() - start
        if verbose:
            usage = response.usage
            typer.echo(f'[DEBUG] Response received in {elapsed:.1f}s')
            typer.echo(
                f'[DEBUG] Tokens: {usage.total_tokens} '
                f'(input: {usage.prompt_tokens}, '
                f'output: {usage.completion_tokens})'
            )
        message = response.choices[0].message.content.strip()
        return clean_markdown_code_blocks(message)
    except Exception as e:
        typer.secho(f'Error calling OpenAI API: {e}', fg=typer.colors.RED)
        exit(1)
