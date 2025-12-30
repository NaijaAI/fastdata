#!/bin/bash
#
# Wrapper script for running pidgin_news.py via cron
# This script:
# - Sets the API key
# - Changes to the correct directory
# - Runs the generator with timestamped output
# - Logs execution details
#

# =============================================================================
# CONFIGURATION
# =============================================================================

# Set your alternate API key here
export OPENROUTER_API_KEY="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"

# Project directory (update this to your actual path)
PROJECT_DIR="/Users/davidokpare/OpenSource/fastdata"

# Log directory
LOG_DIR="${PROJECT_DIR}/pidgin_data/news/logs"

# Python path (adjust if using virtual environment)
# Uncomment and set if you're using a venv:
PYTHON_PATH="${PROJECT_DIR}/.venv/bin/python"
# PYTHON_PATH="python3"

# Number of workers (parallel threads)
# NOTE: Keep at 1 to avoid rate limiting (429 errors)
WORKERS=1

# Number of examples to generate per run
NUM_EXAMPLES=1000

# =============================================================================
# SETUP
# =============================================================================

# Create log directory
mkdir -p "${LOG_DIR}"

# Generate timestamp for logging
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="${LOG_DIR}/run_${TIMESTAMP}.log"

# Change to project directory
cd "${PROJECT_DIR}" || {
    echo "Error: Could not change to ${PROJECT_DIR}" >&2
    exit 1
}

# =============================================================================
# EXECUTION
# =============================================================================

{
    echo "========================================="
    echo "Pidgin News Generator - Cron Run"
    echo "Started: $(date)"
    echo "========================================="
    echo ""

    # Run the generator
    ${PYTHON_PATH} examples/pidgin_news.py \
        --timestamp \
        --workers ${WORKERS} \
        --num ${NUM_EXAMPLES} \
        --output-dir pidgin_data/news

    EXIT_CODE=$?

    echo ""
    echo "========================================="
    echo "Finished: $(date)"
    echo "Exit code: ${EXIT_CODE}"
    echo "========================================="

    exit ${EXIT_CODE}

} 2>&1 | tee "${LOG_FILE}"

# Optional: Clean up old log files (keep last 30 days)
find "${LOG_DIR}" -name "run_*.log" -mtime +30 -delete 2>/dev/null || true
