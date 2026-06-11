# Lonewolf Price History Export

Automatically exports and tracks price history data from the [Lonewolf](https://github.com/researchersec/lonewolf) repository.

## Overview

This repository contains a GitHub Action that:
1. Clones the [researchersec/lonewolf](https://github.com/researchersec/lonewolf.git) repository
2. Runs the `export_price_history.py` script to extract price history from git commits
3. Commits and pushes only the `prices/history` files to this repository

## How It Works

The `export_price_history.py` script:
- Iterates through git commits of `horde.json` in the lonewolf repo
- Extracts pricing data for each item at each commit timestamp
- Generates individual JSON files (`{itemId}.json`) for each item with complete price history
- Creates an `index.json` file listing all items

### Output Structure

```
prices/
├── history/
│   ├── index.json           # Index of all items
│   ├── 12345.json           # Price history for item 12345
│   ├── 12346.json           # Price history for item 12346
│   └── ...
```

### Price History File Format

Each `{itemId}.json` contains:
```json
{
  "itemId": "12345",
  "itemName": "Item Name",
  "priceHistory": [
    {
      "date": "2026-01-15T10:30:00+00:00",
      "timestamp": 1736927400,
      "minBuyout": 1500,
      "marketValue": 1600,
      "quantity": 42,
      "numAuctions": 15
    },
    ...
  ],
  "dataPoints": 125,
  "dateRange": {
    "start": "2026-01-15T10:30:00+00:00",
    "end": "2026-06-11T14:48:00+00:00"
  }
}
```

## Workflow Schedule

The GitHub Action runs:
- **Daily at 2 AM UTC** (automatic)
- **Manual triggers** via workflow dispatch

## Local Usage

To run the export locally:

```bash
# Clone lonewolf
git clone https://github.com/researchersec/lonewolf.git

# Run export
python export_price_history.py
```

### Custom Configuration

Edit `export_price_history.py` to customize:
- `repo_path`: Path to lonewolf repo
- `file_path`: Source JSON file (default: `horde.json`)
- `start_date`: Only include commits after this date
- `output_dir`: Output directory (default: `prices/history`)

## Requirements

- Python 3.7+
- GitPython

Install dependencies:
```bash
pip install GitPython
```

## License

This repository exports data from the [Lonewolf](https://github.com/researchersec/lonewolf) project.
