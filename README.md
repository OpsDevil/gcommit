# 🚀 gcommit

**Stop wasting time writing commit messages. Let AI do it for you.**

`gcommit` is an AI-powered CLI tool that analyzes your staged changes and generates perfect commit messages in seconds. No more staring at a blank screen wondering how to describe your changes.

## ✨ Why You'll Love It

- ⚡ **Instant commit messages** - Generate professional commits in seconds
- 🎯 **Conventional Commits ready** - Perfect for teams following standards
- 🌍 **Any language** - Write commits in English, Russian, Spanish, Chinese, or any language you want
- 🎨 **Customizable** - Simple, conventional, or your own custom format
- 🔧 **Works with any Git workflow** - Local, GitHub, GitLab, Bitbucket, you name it
- 🤖 **Smart context aware** - Analyzes your actual code changes, not just file names
- 💰 **Cheap to run** - Uses efficient models like `gpt-4o-mini` (pennies per month)

## 🎬 Quick Start

```bash
# Install
brew tap opsdevil/tap
brew install opsdevil/tap/gcommit

# Set your OpenAI API key
export OPENAI_API_KEY='sk-your-key-here'

# Stage your changes
git add .

# Let AI write your commit!
gcommit
```

That's it! You'll see a proposed commit message. Type `y` to commit, `e` to edit, or `n` to cancel.

## 🎯 How It Works

1. **Stage your changes** with `git add`
2. **Run** `gcommit`
3. **Review** the AI-generated message
4. **Commit** with one keypress

### Example Session

```bash
$ git add src/auth.py

$ gcommit
Analyzing changes...

Proposed commit message:
feat: add JWT authentication middleware

Implement JWT token validation for protected routes.
Add support for token refresh and blacklist checking.

[y]es / [n]o / [e]dit: y
Committed successfully ✓
```

## 🎨 Commit Message Formats

### Conventional Commits (default)

Perfect for teams and open source projects.

```bash
$ gcommit
feat: add user profile page

Implement user profile with avatar upload and bio editing.
Add validation for profile fields.
```

### Simple Format

Clean and concise, no prefixes.

```bash
$ gcommit --format simple
add user profile page with avatar upload
```

### Custom Format

Define your own template in config file:

```yaml
commit:
  format: custom
  custom_template: |
    [{type}] {subject}
    
    {body}
    
    Signed-off-by: Your Name <your@email.com>
```

## ⚙️ Configuration

Create `~/.gcommit.yaml` for global settings or `.gcommit.yaml` in your project:

```yaml
llm:
  api_key: sk-your-key-here
  model: gpt-4o-mini        # or gpt-4o for even better quality
  temperature: 0.3          # lower = more consistent
  max_tokens: 500

commit:
  language: english         # or spanish, german, etc.
  format: conventional      # conventional, simple, or custom
```

**Priority order:** CLI flags → Environment variables → Local config → Home config → Defaults

### Environment Variables

```bash
export OPENAI_API_KEY='sk-your-key-here'
export OPENAI_BASE_URL='https://api.openai.com/v1'  # optional
export GCOMMIT_MODEL='gpt-4o-mini'
export GCOMMIT_LANGUAGE='english'
export GCOMMIT_FORMAT='conventional'
```

## 🎮 Usage Examples

### Basic Usage

```bash
gcommit                    # Interactive mode (default)
```

### Auto-commit (no confirmation)

```bash
gcommit --auto            # For CI/CD or when you trust the AI
```

### Edit Before Committing

```bash
gcommit --edit            # Opens your $EDITOR to refine the message
```

### Add Context Hint

```bash
gcommit -m "fixing memory leak in cache"
# AI will use your hint to generate better message
```

### Quick Format Override

```bash
gcommit --format simple   # Override config for one commit
```

### Verbose Mode (debugging)

```bash
gcommit --verbose         # See the prompt, API call details, tokens used
```

### Different Model

```bash
gcommit --model gpt-4o    # Use more powerful model for complex changes
```

## 🔥 Pro Tips

### 1. Create an alias
```bash
echo "alias gc='gcommit'" >> ~/.zshrc
# Now just type: gc
```

### 2. Combine with git commands
```bash
git add . && gcommit --auto && git push
```

### 3. Use local config for team standards
```yaml
# .gcommit.yaml in your project
commit:
  language: english
  format: conventional
  
llm:
  model: gpt-4o-mini
  temperature: 0.2  # More consistent for team projects
```

### 4. Review before pushing
```bash
gcommit              # Generate commit
git log -1 --pretty=format:"%B"  # Review last commit message
git push            # Push when satisfied
```

### 5. Works with OpenAI-compatible APIs
```yaml
llm:
  base_url: https://your-llm-proxy.com/v1
  api_key: your-proxy-key
  model: gpt-4o-mini
```

## 🆚 Why Not Just Use Git Copilot / GitHub Copilot?

- **Works everywhere**: Terminal, SSH sessions, any Git hosting
- **Highly customizable**: Your format, your language, your rules
- **Privacy control**: Use your own API keys or self-hosted LLMs
- **Lightweight**: No IDE required, works in pure terminal
- **OpenAI-compatible**: Works with any OpenAI-compatible API

## 🤔 FAQ

<details>
<summary><b>Do I need an OpenAI API key?</b></summary>

Yes, but it's very affordable! Using `gpt-4o-mini`, you'll spend pennies even with dozens of commits per day. Get your key at https://platform.openai.com/api-keys
</details>

<details>
<summary><b>Can I use other LLM providers?</b></summary>

Yes! Set `base_url` in your config to any OpenAI-compatible API endpoint (Anthropic, local models via Ollama, etc.)
</details>

<details>
<summary><b>Will it commit automatically?</b></summary>

No, by default it asks for confirmation. Use `--auto` flag only when you trust the AI completely.
</details>

<details>
<summary><b>What if I don't like the generated message?</b></summary>

Press `e` to edit in your favorite editor, or `n` to cancel and write manually.
</details>

<details>
<summary><b>Does it work with pre-commit hooks?</b></summary>

Yes! The commit is made via standard git, so all hooks run normally.
</details>

<details>
<summary><b>Can I use it for multiple commits?</b></summary>

Absolutely! Stage the specific files you want (`git add file1 file2`) and run `gcommit`.
</details>

## 🤝 Contributing

Found a bug? Have a feature request? PRs and issues welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing`)
3. Make your changes
4. Use `gcommit` to commit 😉
5. Push and open a PR

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

## ⭐ Show Your Support

If `gcommit` saves you time, give it a star on GitHub! It helps others discover the tool.

---

**Made with ❤️ by developers who are tired of writing commit messages**

[Report Bug](https://github.com/OpsDevil/gcommit/issues) · [Request Feature](https://github.com/OpsDevil/gcommit/issues) · [Documentation](https://github.com/OpsDevil/gcommit)
