# GeminiWatch

A terminal-based Gemini CLI monitoring dashboard.

## Features
- **Zero Configuration**: Automatically discovers Gemini CLI session logs.
- **Usage Tracking**: Monitor input/output tokens, request counts, and estimated costs.
- **Historical Data**: Persistent SQLite database stores all past activity.
- **Non-Invasive**: No shell aliases or wrappers required.

## Installation
The `geminiwatch` binary is located in `bin/`. You can symlink it to your path:
```bash
ln -s $(pwd)/bin/geminiwatch /usr/local/bin/geminiwatch
```

## Usage
- `geminiwatch`: Show a summary of today's and lifetime usage.
- `geminiwatch dashboard`: Open a live-refreshing dashboard.
- `geminiwatch sync`: Manually trigger a sync from Gemini session files.
- `geminiwatch export --format csv`: Export all data to CSV.

## Data Source
GeminiWatch monitors `~/.gemini/tmp/*/chats/session-*.json` files created by the Gemini CLI.