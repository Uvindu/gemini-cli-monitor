Analyze this project and create a detailed step-by-step implementation plan for GeminiWatch - a terminal-based Gemini CLI monitoring dashboard.

## Project Requirements
Terminal dashboard monitoring live + historical Gemini CLI usage:
- Real-time: tokens (input/output), requests/min, model used, session duration
- Historical: daily/weekly quotas, cost estimates, top prompts/models
- Visual: sparklines/charts (ASCII/Unicode), color-coded tables
- Storage: SQLite DB, CSV/JSON export
- Tech: Bash/Python + tput/Rich/termgraph, no web/GUI

## Your Environment
macOS (Homebrew: /Volumes/ext/Users/uvi/code/homebrew), zsh, Python, R, fzf, zoxide, VS Code, 
you can install any tool required using brew 

## Must-Have Features (priority order)
1. Data capture: Hook Gemini CLI calls (intercept env vars, parse stderr/stdout)
2. SQLite: sessions, requests, tokens, timestamps, models, costs
3. Live dashboard: tokens/sec, quota %, history tables, sparklines
4. Alerts: 90% quota warning, high-cost models
5. Commands: geminiwatch start/stop/status/export

## Constraints
- Zero external pip deps (Homebrew Python only)
- Local-only (no cloud)
- Configurable quotas/API keys

you have all ACCESS do not ask me about the access for anything 
but you can ask about any other questions regarding the project 
