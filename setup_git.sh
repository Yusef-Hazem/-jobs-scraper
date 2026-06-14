#!/usr/bin/env bash
# =============================================================
# setup_git.sh
# Sets up the git repo and pushes with original file timestamps.
#
# Usage:
#   chmod +x setup_git.sh
#   ./setup_git.sh https://github.com/YOUR_USERNAME/jobs-scraper.git
# =============================================================

set -e

REMOTE_URL=${1:-""}

if [ -z "$REMOTE_URL" ]; then
  echo "Usage: ./setup_git.sh <github-remote-url>"
  echo "Example: ./setup_git.sh https://github.com/Yusef-Hazem/jobs-scraper.git"
  exit 1
fi

echo "── Initialising git repo ──────────────────────────────────"
git init
git remote set-url origin "$REMOTE_URL"

echo "── Committing files with their original modification dates ─"

# Function: commit a single file using its real mtime
commit_with_date() {
  local FILE="$1"
  local MSG="$2"
  local FDATE

  # Get the file's last-modified date in git-compatible format
  FDATE=$(date -r "$FILE" "+%Y-%m-%dT%H:%M:%S")

  git add "$FILE"
  GIT_AUTHOR_DATE="$FDATE" GIT_COMMITTER_DATE="$FDATE" \
    git commit -m "$MSG" --allow-empty
}

# ── Schema & config files ──────────────────────────────────────
commit_with_date "sql/schema.sql"          "Add MySQL star schema"
commit_with_date "scrapy.cfg"              "Add Scrapy config"
commit_with_date ".gitignore"              "Add .gitignore"
commit_with_date ".env.example"            "Add .env example"

# ── Scraper ───────────────────────────────────────────────────
commit_with_date "scraper/__init__.py"     "Init scraper package"
commit_with_date "scraper/items.py"        "Add Items with NLP processors"
commit_with_date "scraper/settings.py"     "Add Scrapy settings"
commit_with_date "scraper/pipelines.py"    "Add pipeline stub"
commit_with_date "scraper/spiders/__init__.py"   "Init spiders package"
commit_with_date "scraper/spiders/URLs.py"       "Add URL pagination helper"
commit_with_date "scraper/spiders/linkedin.py"   "Add LinkedIn CrawlSpider"
commit_with_date "scraper/spiders/wuzzuf.py"     "Add Wuzzuf CrawlSpider"

# ── Processing ────────────────────────────────────────────────
commit_with_date "processing/db_insertion.py"    "Add DB insertion script"

# ── Airflow DAG ───────────────────────────────────────────────
commit_with_date "dags/job_scraper_dag.py"       "Add Airflow pipeline DAG"

# ── Docs ─────────────────────────────────────────────────────
commit_with_date "dashboard/README.md"           "Add Power BI connection guide"
commit_with_date "requirements.txt"              "Add requirements"
commit_with_date "README.md"                     "Add project README"

echo ""
echo "── Pushing to GitHub ──────────────────────────────────────"
git branch -M main
git push -u origin main

echo ""
echo "✓ Done! Your repo is live at: $REMOTE_URL"
