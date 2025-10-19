"""LLM integration module"""
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import typer
import yaml
from openai import OpenAI


@dataclass
class Config:
    """Application configuration"""
    openai_api_key: str
    base_url: str = None
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 500
    language: str = "english"
    commit_format: str = "conventional"
    custom_template: Optional[str] = None


def find_local_config() -> Optional[Path]:
    """Find .gcommit.yaml in current dir or up to git repo root"""
    current = Path.cwd()

    # Search up to git root or filesystem root
    for parent in [current] + list(current.parents):
        config_file = parent / ".gcommit.yaml"
        if config_file.exists():
            return config_file

        # Stop at git root
        git_dir = parent / ".git"
        if git_dir.exists():
            break

    return None


def load_config(
    model: Optional[str] = None,
    language: Optional[str] = None,
    commit_format: Optional[str] = None
) -> Config:
    """Load configuration with priority: CLI > ENV > Local > Home > Defaults"""

    # Load home config
    home_config_path = Path.home() / ".gcommit.yaml"
    home_config = {}
    if home_config_path.exists():
        try:
            with open(home_config_path, encoding="utf-8") as f:
                home_config = yaml.safe_load(f) or {}
        except Exception as e:
            typer.secho(f"Warning: Could not read home config: {e}", fg=typer.colors.YELLOW)

    # Load local config
    local_config_path = find_local_config()
    local_config = {}
    if local_config_path:
        try:
            with open(local_config_path, encoding="utf-8") as f:
                local_config = yaml.safe_load(f) or {}
        except Exception as e:
            typer.secho(f"Warning: Could not read local config: {e}", fg=typer.colors.YELLOW)

    # Merge configs: local overrides home
    llm_config = {**home_config.get("llm", {}),
                  **local_config.get("llm", {})}
    commit_config = {**home_config.get("commit", {}),
                     **local_config.get("commit", {})}

    # Merge with env vars (higher priority than file)
    api_key = (os.getenv("OPENAI_API_KEY") or llm_config.get("api_key"))
    base_url = (os.getenv("OPENAI_BASE_URL") or llm_config.get("base_url"))
    model_name = (os.getenv("GCOMMIT_MODEL") or llm_config.get("model", "gpt-4o-mini"))
    temperature = float(os.getenv("GCOMMIT_TEMPERATURE", llm_config.get("temperature", 0.3)))
    max_tokens = int(os.getenv("GCOMMIT_MAX_TOKENS", llm_config.get("max_tokens", 500)))
    lang = (os.getenv("GCOMMIT_LANGUAGE") or commit_config.get("language", "english"))
    fmt = (os.getenv("GCOMMIT_FORMAT") or commit_config.get("format", "conventional"))
    custom_template = commit_config.get("custom_template")

    # CLI args override everything (highest priority)
    if model:
        model_name = model
    if language:
        lang = language
    if commit_format:
        fmt = commit_format

    # Validate API key
    if not api_key:
        typer.secho("Error: OPENAI_API_KEY not found", fg=typer.colors.RED)
        typer.echo("Set it via:")
        typer.echo("   - Environment: export OPENAI_API_KEY='your-key'")
        typer.echo("   - Config file: ~/.gcommit.yaml")
        exit(1)

    return Config(
        openai_api_key=api_key,
        base_url=base_url,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        language=lang,
        commit_format=fmt,
        custom_template=custom_template
    )


def build_prompt(
    staged_files: List[str],
    diff: str,
    config: Config,
    user_hint: Optional[str] = None
) -> str:
    """Build prompt for LLM"""
    files_list = ', '.join(staged_files)

    # Format-specific instructions
    format_instructions = {
        "conventional": """
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
        "simple": """
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

    if config.commit_format == "custom":
        if config.custom_template:
            format_instructions["custom"] = f"""
Use the following custom template for commit message:

{config.custom_template}

Follow the template structure and fill with appropriate content based on the changes.
"""
        else:
            typer.secho(
                "Error: custom_template not configured for "
                "'custom' format",
                fg=typer.colors.RED
            )
            exit(1)

    instructions = format_instructions.get(
        config.commit_format,
        format_instructions["conventional"]
    )

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
    if text.startswith("```") and text.endswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        text = "\n".join(lines[1:-1])

    return text.strip()


def generate_commit_message(
    staged_files: List[str],
    diff: str,
    config: Config,
    user_hint: Optional[str] = None,
    verbose: bool = False
) -> str:
    """Generate commit message using OpenAI API"""
    prompt = build_prompt(staged_files, diff, config, user_hint)
    if verbose:
        typer.echo("[DEBUG] Prompt:")
        typer.echo("=" * 80)
        typer.echo(prompt)
        typer.echo("=" * 80)
        typer.echo(f"[DEBUG] Calling OpenAI API "
                   f"(model: {config.model}, temp: {config.temperature})")
    try:
        start = time.time()
        client = OpenAI(api_key=config.openai_api_key, base_url=config.base_url)
        response = client.chat.completions.create(
            model=config.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )
        elapsed = time.time() - start
        if verbose:
            usage = response.usage
            typer.echo(f"[DEBUG] Response received in {elapsed:.1f}s")
            typer.echo(f"[DEBUG] Tokens: {usage.total_tokens} "
                       f"(input: {usage.prompt_tokens}, "
                       f"output: {usage.completion_tokens})")
        message = response.choices[0].message.content.strip()
        return clean_markdown_code_blocks(message)
    except Exception as e:
        typer.secho(f"Error calling OpenAI API: {e}", fg=typer.colors.RED)
        exit(1)
