"""Configuration management module"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer
import yaml


@dataclass
class Config:
    """Application configuration"""

    openai_api_key: str
    base_url: str = None
    model: str = 'gpt-4o-mini'
    temperature: float = 0.3
    max_tokens: int = 500
    language: str = 'english'
    commit_format: str = 'conventional'
    custom_template: Optional[str] = None


def find_local_config() -> Optional[Path]:
    """Find .gcommit.yaml in current dir or up to git repo root"""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        config_file = parent / '.gcommit.yaml'
        if config_file.exists():
            return config_file
        git_dir = parent / '.git'
        if git_dir.exists():
            break
    return None


def create_default_config(path: Path) -> None:
    """Create default configuration file"""
    path.parent.mkdir(parents=True, exist_ok=True)

    default_config = """llm:
  api_key: sk-your-key-here
  model: gpt-4o-mini
  temperature: 0.3
  max_tokens: 500

commit:
  language: english
  format: conventional
"""

    with open(path, 'w', encoding='utf-8') as f:
        f.write(default_config)


def load_config(
    config_path: Optional[str] = None, 
    model: Optional[str] = None, 
    language: Optional[str] = None, 
    commit_format: Optional[str] = None
) -> Config:
    """Load configuration with priority: CLI > ENV > Local > XDG Home > Defaults"""
    if config_path:
        home_config_path = Path(config_path)
    elif os.getenv('GCOMMIT_CONFIG'):
        home_config_path = Path(os.getenv('GCOMMIT_CONFIG'))
    else:
        xdg_config_home = os.getenv('XDG_CONFIG_HOME', str(Path.home() / '.config'))
        home_config_path = Path(xdg_config_home) / 'gcommit' / 'config.yaml'

    # Load home config
    home_config = {}
    if home_config_path.exists():
        try:
            with open(home_config_path, encoding='utf-8') as f:
                home_config = yaml.safe_load(f) or {}
        except Exception as e:
            typer.secho(f'Error reading config file {home_config_path}: {e}', fg=typer.colors.RED)
            sys.exit(1)
    else:
        # If a config file was explicitly provided but doesn't exist, error out
        if config_path or os.getenv('GCOMMIT_CONFIG'):
            typer.secho(f'Error: Config file not found: {home_config_path}', fg=typer.colors.RED)
            sys.exit(1)
        # Otherwise, create default config
        try:
            create_default_config(home_config_path)
            typer.secho(f'Created default config at {home_config_path}', fg=typer.colors.GREEN)
            typer.echo('Please edit the config file and set your OpenAI API key.')
            with open(home_config_path, encoding='utf-8') as f:
                home_config = yaml.safe_load(f) or {}
        except Exception as e:
            typer.secho(f'Error creating default config: {e}', fg=typer.colors.RED)
            sys.exit(1)
    local_config_path = find_local_config()
    local_config = {}
    if local_config_path:
        try:
            with open(local_config_path, encoding='utf-8') as f:
                local_config = yaml.safe_load(f) or {}
        except Exception as e:
            typer.secho(f'Warning: Could not read local config: {e}', fg=typer.colors.YELLOW)

    # Merge configs: local overrides home
    llm_config = {**home_config.get('llm', {}), **local_config.get('llm', {})}
    commit_config = {**home_config.get('commit', {}), **local_config.get('commit', {})}

    # Merge with env vars (higher priority than file)
    api_key = os.getenv('OPENAI_API_KEY') or llm_config.get('api_key')
    base_url = os.getenv('OPENAI_BASE_URL') or llm_config.get('base_url')
    model_name = os.getenv('GCOMMIT_MODEL') or llm_config.get('model', 'gpt-4o-mini')
    temperature = float(os.getenv('GCOMMIT_TEMPERATURE', llm_config.get('temperature', 0.3)))
    max_tokens = int(os.getenv('GCOMMIT_MAX_TOKENS', llm_config.get('max_tokens', 500)))
    lang = os.getenv('GCOMMIT_LANGUAGE') or commit_config.get('language', 'english')
    fmt = os.getenv('GCOMMIT_FORMAT') or commit_config.get('format', 'conventional')
    custom_template = commit_config.get('custom_template')

    # CLI args override everything (highest priority)
    if model:
        model_name = model
    if language:
        lang = language
    if commit_format:
        fmt = commit_format

    # Validate API key
    if not api_key:
        typer.secho('Error: OPENAI_API_KEY not found', fg=typer.colors.RED)
        typer.echo('Set it via:')
        typer.echo("  - Environment: export OPENAI_API_KEY='your-key'")
        typer.echo(f'  - Config file: {home_config_path}')
        sys.exit(1)

    return Config(
        openai_api_key=api_key,
        base_url=base_url,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        language=lang,
        commit_format=fmt,
        custom_template=custom_template,
    )
