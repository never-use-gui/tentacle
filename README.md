# Tentacle 🐙

A powerful Textual-based TUI (Terminal User Interface) for viewing and managing git diffs with **AI-powered commit message generation** using GAC (Git Auto Commit).

## ⌨️ Keybindings

### 📁 File Navigation
- `↑/↓` - Navigate through files and hunks
- `Enter` - Select file to view diff
- `Tab` - Navigate through UI elements (use `Shift+Tab` to go backwards)
- `1` or `Ctrl+1` - Switch to **Unstaged Changes** tab
- `2` or `Ctrl+2` - Switch to **Staged Changes** tab

### 🔄 Git Operations
- `s` - Stage selected file
- `u` - Unstage selected file
- `a` - **Stage ALL unstaged changes**
- `x` - **Unstage ALL staged changes**
- `c` - Commit staged changes

### 🌿 Branch Management
- `b` - Show branch switcher
- `r` - Refresh branches

### 📡 Remote Operations
- `p` - Push current branch
- `o` - Pull latest changes

### 🤖 AI Integration (GAC)
- `Ctrl+G` - **Configure GAC** (Git Commit Assistant)
- `g` - **Generate commit message with AI**

### ⚙️ Application
- `h` - **Show help modal** with all keybindings
- `r` - Refresh git status and file tree
- `q` - Quit application

## ✨ Features

### Core Git Features
- **Modern Tabbed UI**: Separate tabs for Unstaged/Staged changes with easy switching (`1`/`2` keys)
- **Spacious Commit Editor**: Large commit message (6 lines) and body (10 lines) text areas for detailed commits
- **Hunk-based staging**: Stage, unstage, or discard individual hunks
- **Branch management**: View, switch between branches
- **Commit history**: Browse commit history with details
- **Real-time git status**: Color-coded file status indicators

### 🤖 AI-Powered Commits with GAC
- **AI-generated commit messages**: Press `g` to generate a suggested commit message (no auto-commit)
- **21+ AI providers**: Anthropic, Cerebras, Chutes, Claude-Code, Custom-Anthropic, Custom-OpenAI, DeepSeek, Fireworks, Gemini, Groq, LM-Studio, MiniMax, Mistral, Ollama, OpenAI, OpenRouter, StreamLake, Synthetic, Together, Zai, Zai-Coding, and more!
- **Dynamic provider discovery**: Automatically detects all available GAC providers
- **Optional dependency**: Works great without GAC; install separately for AI features
- **Smart configuration**: Easy setup through built-in modal (Ctrl+G)
- **Context-aware**: Generates messages based on your actual code changes
- **Graceful degradation**: App works perfectly even if GAC isn't installed

## 🎨 Git Status Colors

- **🟢 Green**: Staged files (ready to commit)
- **🟡 Yellow**: Modified files (unstaged changes)
- **🔵 Blue**: Directories
- **🟣 Purple**: Untracked files
- **🔴 Red**: Deleted files

## 🚀 Usage

```bash
# Run Tentacle with UV (recommended)
uv run tentacle [repo_path]

# Or run directly with Python module syntax
uv run python -m tentacle.main [repo_path]
```

## ⌨️ Controls

### Basic Navigation
- `q` - Quit the application
- `Ctrl+d` - Toggle dark mode
- `r` - Refresh branches
- `b` - Switch branch

### Git Operations
- `c` - Commit staged changes (manual message)
- `g` - **GAC Generate Message** (AI-suggested commit message, no auto-commit)
- `Ctrl+G` - **Configure GAC** settings

### File Operations
- Click files to view diffs
- Use hunk buttons to stage/unstage/discard changes
- Stage entire files or individual hunks

## 🤖 Setting Up GAC (AI Commits)

### Installation

GAC is **optional** but highly recommended for AI-powered commit messages:

```bash
# Install GAC with UV
uv pip install 'gac>=0.18.0'
```

### Configuration

1. **Open Tentacle** in your git repository
2. **Press `Ctrl+G`** to open GAC configuration
3. **Choose your provider** from 21+ supported options:
   - **Cerebras**: Qwen3-Coder-480B (recommended for code, 1M free tokens/day)
   - **OpenAI**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
   - **Anthropic**: Claude-3.5-Sonnet, Claude-3.5-Haiku, Claude-3-Opus
   - **Groq**: Llama-3.3-70B, Mixtral-8x7B (fast & free)
   - **DeepSeek**: DeepSeek-V3, DeepSeek-Chat (great for code)
   - **Gemini**: Gemini-2.0-Flash, Gemini-Pro
   - **Ollama**: Local models (llama3.2, qwen2.5, etc.)
   - **OpenRouter**: Access to 100+ models
   - **Fireworks**: Fast inference on open models
   - **Together**: Llama, Qwen, and more
   - **Mistral**: Mistral-Large, Mistral-Small, Codestral
   - **And more**: Chutes, Claude-Code, Custom-Anthropic, Custom-OpenAI, LM-Studio, MiniMax, StreamLake, Synthetic, Zai, Zai-Coding
4. **Select a model** from the dropdown
5. **Paste your API key** directly into the config modal (or leave blank for local providers like Ollama)
6. **Click Save**

### Cerebras: Recommended for GAC

Cerebras' Qwen3-Coder-480B model is well-suited for commit message generation:

- Free tier with 1 million tokens per day (no credit card required)
- Optimized specifically for code-related tasks
- Fast response times
- Get your API key: https://cloud.cerebras.ai/

## 🔧 Installation

This project uses **UV** for Python environment management and **Walmart's internal PyPI**.

```bash
# Clone the repository
git clone <tentacle-repo>
cd tentacle

# Install with UV
uv sync

# Run the application
uv run tentacle
```

## 📦 Dependencies

### Required
- **textual>=6.1.0** - Modern TUI framework
- **GitPython>=3.1.42** - Git repository operations

### Optional
- **gac>=0.18.0** - AI-powered commit message generation
  - Install with: `uv pip install 'gac>=0.18.0'`
  - Enables AI commit message generation with 21+ provider options
  - Tentacle works perfectly without it!

## 🎯 Workflow Example

1. **Open Tentacle**: `uv run tentacle`
2. **Make some changes** to your code
3. **Review diffs** in the center panel
4. **Stage hunks** by clicking "Stage" buttons
5. **Press `g`** for AI-generated commit message
6. **Boom!** 🎉 Professional commit message is generated and filled in—review/edit, then press Commit

## 🔮 What Makes This Special

Tentacle combines the power of a visual git interface with AI-powered commit messages, making it perfect for:

- **Code reviews**: Visual diff inspection with hunk-level control
- **Professional commits**: AI generates conventional commit messages
- **Fast workflow**: Stage, review, and commit without leaving the terminal
- **Team consistency**: Standardized commit message formats

---

**Built with ❤️*

*"Because managing git shouldn't require a kraken!"* 🐙
