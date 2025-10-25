"""LLM integration module"""

import time
from pathlib import Path
from typing import List, Optional

import typer
from openai import OpenAI

from gcommit.config import Config, load_config


def load_prompt(format_name: str) -> str:
    """Load prompt template from file"""
    prompts_dir = Path(__file__).parent / 'prompts'
    prompt_file = prompts_dir / f'{format_name}.txt'
    if prompt_file.exists():
        return prompt_file.read_text()
    return (prompts_dir / 'conventional.txt').read_text()


def build_prompt(
    staged_files: List[str], diff: str, branch_name: str, config: Config, user_hint: Optional[str] = None
) -> str:
    """Build prompt for LLM"""
    files_list = ', '.join(staged_files)
    if config.commit_format == 'custom':
        if config.custom_template:
            instructions = load_prompt('custom').format(template=config.custom_template)
        else:
            typer.secho("Error: custom_template not configured for 'custom' format", fg=typer.colors.RED)
            exit(1)
    else:
        instructions = load_prompt(config.commit_format)
    base_template = load_prompt('base')

    user_context = ''
    if user_hint:
        user_context = (
            f'User context: {user_hint}\n(Use this as additional context to understand the changes better)\n\n'
        )

    return base_template.format(
        language=config.language,
        instructions=instructions,
        user_context=user_context,
        files_list=files_list,
        branch_name=branch_name,
        diff=diff,
    )


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
    staged_files: List[str],
    diff: str,
    branch_name: str,
    config: Config,
    user_hint: Optional[str] = None,
    verbose: bool = False,
) -> str:
    """Generate commit message using OpenAI API"""
    prompt = build_prompt(staged_files, diff, branch_name, config, user_hint)
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
