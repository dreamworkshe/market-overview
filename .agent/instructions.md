# Project Instructions: Market Overview

## 🐍 Environment & Python
- **Mandatory venv**: This project MUST use the virtual environment located at `./.venv`.
- **Command Pattern**: ALWAYS use the absolute or relative path to the venv's python executable:
  - `$(pwd)/.venv/bin/python3 scripts/fetch_data.py`
  - Avoid global `python3` or `pip3`.
- **Dependencies**: New dependencies should be added to `scripts/requirements.txt` AND installed in `.venv`.

## 📊 Data Management
- **Primary Data**: `data/history.json` is the source of truth for the dashboard.
- **Daily Updates**: GitHub Actions update this file daily (UTC 23:00 / TPE 07:00).
- **No Overwriting**: NEVER push an older version of `data/history.json` to the repo. 
- **Sync Workflow**: Always use the `/抓取repo` command (`git pull origin main --rebase`) before starting work or pushing changes.

## 🕸️ Web Scraping (`scripts/fetch_data.py`)
- **Technology**: Uses **Playwright (Chromium)** to bypass anti-bot measures and render JS.
- **Fail-safe Logic**: If new data is not found (`None`), the script MUST NOT overwrite existing data with old values. It should retain the previous valid entries or leave as `null`.

## 🚀 GitHub Actions
- **Workflow**: `.github/workflows/daily_update.yml`.
- **Responsibility**: It runs the fetcher, generates the HTML pages, and pushes them back to the repository.
- **Permissions**: Ensure it has `contents: write` permission for pushing updates.
