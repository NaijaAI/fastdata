# Cron Job Setup for Pidgin News Generator

This guide explains how to set up a daily cron job to automatically generate Nigerian Pidgin news/formal content.

## Files Created

1. **`pidgin_news.py`** - Main generator script with formal topics (news, lectures, articles, etc.)
   - **4.3 million+ unique combinations** (40 topics × 15 genres × 12 settings × 10 tones × 15 speakers × 5 time periods × 8 complexity levels)
   - Focused on formal/professional content: news reports, financial analysis, lectures, announcements, etc.
   - Uses daily seed for variation
   
2. **`run_pidgin_news.sh`** - Wrapper script for cron execution
   - Handles API key configuration
   - Generates timestamped output files
   - Creates execution logs
   - Automatically cleans old logs

## Setup Steps

### 1. Configure the Wrapper Script

Edit `examples/run_pidgin_news.sh` and update:

```bash
# Set your alternate API key
export OPENROUTER_API_KEY="your-actual-api-key-here"

# Verify project directory (should be correct)
PROJECT_DIR="/Users/davidokpare/OpenSource/fastdata"

# Optional: Adjust workers and number of examples
WORKERS=4
NUM_EXAMPLES=1000
```

### 2. Test the Script Manually

Before setting up cron, test that everything works:

```bash
cd /Users/davidokpare/OpenSource/fastdata
./examples/run_pidgin_news.sh
```

This should:
- Create `pidgin_data/news/` directory
- Generate `data_YYYY-MM-DD_HH-MM-SS.jsonl` with 1000 examples
- Create a log file in `pidgin_data/news/logs/`

### 3. Set Up the Cron Job

Open your crontab for editing:

```bash
crontab -e
```

Add one of these lines depending on when you want it to run:

#### Daily at 2:00 AM
```cron
0 2 * * * /Users/davidokpare/OpenSource/fastdata/examples/run_pidgin_news.sh
```

#### Daily at midnight
```cron
0 0 * * * /Users/davidokpare/OpenSource/fastdata/examples/run_pidgin_news.sh
```

#### Daily at 6:00 AM
```cron
0 6 * * * /Users/davidokpare/OpenSource/fastdata/examples/run_pidgin_news.sh
```

#### Every 12 hours (at 2am and 2pm)
```cron
0 2,14 * * * /Users/davidokpare/OpenSource/fastdata/examples/run_pidgin_news.sh
```

Save and exit the editor (`:wq` in vim, or `Ctrl+X` then `Y` in nano).

### 4. Verify Cron Job is Scheduled

List your cron jobs:

```bash
crontab -l
```

You should see your new entry.

## Output Structure

After running, you'll have:

```
pidgin_data/news/
├── data_2025-12-29_02-00-01.jsonl       # Generated data (timestamped)
├── data_2025-12-30_02-00-01.jsonl       # Next day's data
├── failed_2025-12-29_02-00-01.jsonl     # Any failures (if they occur)
└── logs/
    ├── run_2025-12-29_02-00-01.log      # Execution log
    └── run_2025-12-30_02-00-01.log      # Next day's log
```

## Understanding the Data

Each run generates **1000 unique examples** from **4.3 million possible combinations**, using:

### Topics (40 formal topics)
- Politics: elections, government, policy, corruption investigations
- Economy: stock market, banking, startups, unemployment, inflation
- Technology: fintech, AI, cybersecurity, digital transformation
- Education: university research, reforms, scholarships
- Health: medical breakthroughs, public health, pharmaceuticals
- Law: court proceedings, legal reforms, human rights
- Environment: climate change, pollution, renewable energy

### Genres (15 formal formats)
- News reports, breaking news, investigative articles
- Expert analysis, editorial opinions, feature stories
- Press conferences, public lectures, financial reports
- Research presentations, policy briefings, market updates

### Additional Dimensions
- 12 professional settings (newsroom, government house, corporate office, etc.)
- 10 professional tones (authoritative, analytical, investigative, etc.)
- 15 professional speakers (journalists, analysts, professors, experts)
- 5 time contexts (breaking, recent, ongoing, historical, future)
- 8 complexity levels (executive summary, detailed analysis, technical deep-dive, etc.)

## Daily Variation

The script uses the current date as a random seed, so:
- **Different examples each day** from the same combination space
- **1000 examples/day** = would take **4,320 days** (~12 years) to exhaust all combinations
- Each day's run is **completely independent** and can be pushed to HuggingFace separately

## Managing the Output Files

### Pushing to HuggingFace

Since files are timestamped, you can push them individually:

```bash
# Push a specific day's data
huggingface-cli upload your-username/pidgin-news \
    pidgin_data/news/data_2025-12-29_02-00-01.jsonl

# Or combine multiple days
cat pidgin_data/news/data_2025-*.jsonl > combined.jsonl
```

### Cleaning Up

Old logs are automatically cleaned (kept for 30 days). To manually clean:

```bash
# Remove logs older than 30 days
find pidgin_data/news/logs -name "run_*.log" -mtime +30 -delete

# Archive old data files
mkdir -p archives/
mv pidgin_data/news/data_2025-11-*.jsonl archives/
```

## Troubleshooting

### Cron job not running?

1. Check cron is running:
   ```bash
   sudo launchctl list | grep cron
   ```

2. Check system logs:
   ```bash
   log show --predicate 'process == "cron"' --last 1d
   ```

3. Verify the script path is absolute in crontab

### API key issues?

Make sure the API key in `run_pidgin_news.sh` is correct and has proper quotes.

### Permission errors?

Ensure the script is executable:
```bash
chmod +x /Users/davidokpare/OpenSource/fastdata/examples/run_pidgin_news.sh
```

### Check the logs!

Execution logs are saved in `pidgin_data/news/logs/` - check these first when debugging.

## Customization

You can modify `run_pidgin_news.sh` to:
- Change `WORKERS` (default: 4) for faster/slower generation
- Change `NUM_EXAMPLES` (default: 1000) for more/fewer examples per run
- Adjust log retention period (default: 30 days)
- Use a Python virtual environment by setting `PYTHON_PATH`

## Monitoring

To monitor your cron job:

```bash
# Watch for new files
watch -n 60 'ls -lh pidgin_data/news/data_*.jsonl | tail -5'

# Check latest log
tail -f pidgin_data/news/logs/run_*.log | tail -1

# Count total examples generated
wc -l pidgin_data/news/data_*.jsonl
```
