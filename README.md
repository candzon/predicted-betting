# Understat Betting Analysis Scraper

A robust web scraper for Understat.com designed to feed betting analysis tools with accurate team statistics including Expected Goals (xG) metrics.

## Features

- 🚀 **Fast Scraping**: Uses `requests` and `BeautifulSoup` (no Selenium overhead)
- 📊 **Comprehensive Data**: Extracts xG, xGA, xPTS, and traditional statistics
- 💾 **SQLite Storage**: Prisma ORM with async operations
- 🔄 **Upsert Logic**: Prevents duplicates, updates existing records
- 📝 **Detailed Logging**: Track scraping progress and errors
- 🎯 **Multi-League Support**: EPL, La Liga, Serie A, Bundesliga, Ligue 1, RFPL

## Tech Stack

- Python 3.8+
- requests & beautifulsoup4
- prisma-client-py
- asyncio
- SQLite

## Installation

1. **Install Python dependencies**:
```bash
pip install requests beautifulsoup4 lxml prisma
```

2. **Generate Prisma client**:
```bash
prisma generate --schema=schema.prisma
```

3. **Create database**:
```bash
prisma db push --schema=schema.prisma
```

## Project Structure

```
predicted-betting/
├── schema.prisma              # Prisma schema with TeamStats model
├── understat_scraper.py       # Scraper class (no Selenium)
├── main.py                    # Main orchestration script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── betting_analysis.db        # SQLite database (generated)
```

## Usage

### Basic Usage

Scrape all configured leagues for the current season:

```bash
python main.py
```

### Configuration

Edit `main.py` to customize:

```python
LEAGUES = [
    "EPL",         # English Premier League
    "La_liga",     # Spanish La Liga
    "Serie_A",     # Italian Serie A
    "Bundesliga",  # German Bundesliga
    "Ligue_1",     # French Ligue 1
    "RFPL"         # Russian Premier League
]

SEASON = 2025  # Target season
```

### Scrape Single League

```python
import asyncio
from main import scrape_single_league

asyncio.run(scrape_single_league("EPL", 2025))
```

### Standalone Scraper

```python
from understat_scraper import UnderstatScraper

with UnderstatScraper() as scraper:
    data = scraper.fetch_data("EPL", 2025)
    print(f"Scraped {len(data)} teams")
```

## Database Schema

### TeamStats Model

| Field    | Type   | Description                          |
|----------|--------|--------------------------------------|
| id       | Int    | Auto-increment primary key           |
| league   | String | League name (EPL, La_liga, etc.)     |
| season   | Int    | Season year (2025, 2024, etc.)       |
| teamName | String | Team name                            |
| matches  | Int    | Total matches played                 |
| wins     | Int    | Wins                                 |
| draws    | Int    | Draws                                |
| loses    | Int    | Losses                               |
| scored   | Int    | Goals scored                         |
| missed   | Int    | Goals conceded                       |
| xG       | Float  | Expected Goals (betting metric)      |
| xGA      | Float  | Expected Goals Against               |
| xPTS     | Float  | Expected Points                      |

**Unique Constraint**: `(teamName, league, season)` prevents duplicates

## How It Works

### 1. URL Construction
```
https://understat.com/league/{LEAGUE}/{SEASON}
```

### 2. Data Extraction

Understat stores data in JavaScript variables within `<script>` tags:

```javascript
var teamsData = JSON.parse('\x5b\x7b...\x7d\x5d');
```

The scraper:
- Fetches the HTML page
- Locates script tags containing `teamsData`
- Extracts the hex-encoded JSON string
- Decodes unicode escapes (`\xHH`)
- Parses the clean JSON data

### 3. Database Operations

Uses Prisma's `upsert` to:
- **Insert** new team records
- **Update** existing records (based on unique constraint)
- Avoid duplicate entries

## Output Example

```
2026-01-18 10:30:15 - INFO - Fetching data from: https://understat.com/league/EPL/2025
2026-01-18 10:30:17 - INFO - Successfully extracted 20 teams for EPL 2025
2026-01-18 10:30:18 - INFO - ✓ Scraped 20 teams for EPL 2025

============================================================
SCRAPING SUMMARY
============================================================
Season: 2025
Leagues processed: 6/6
Total teams scraped: 120
============================================================

Sample data from database:

Top xG Team: Manchester City (EPL)
  Matches: 38
  xG: 95.42 | xGA: 28.15 | xPTS: 89.3
  Record: 28W-5D-5L
  Goals: 99 scored, 33 conceded
```

## Troubleshooting

### Prisma Client Not Found

```bash
prisma generate --schema=schema.prisma
```

### HTTP Errors (403, 429)

The scraper includes realistic User-Agent headers. If you encounter rate limiting:
- Add delays between requests
- Reduce the number of leagues scraped at once

### Missing Data

Understat occasionally changes variable names. The scraper includes fallback extraction methods for `datesData` and other variables.

## Betting Use Cases

The extracted xG metrics are crucial for:

- **Value Betting**: Compare xG vs actual goals to find overperforming/underperforming teams
- **Expected Points Model**: xPTS indicates "true" team strength beyond luck
- **Over/Under Predictions**: xG + xGA provides expected total goals
- **Team Form Analysis**: Track xG trends across matches

## License

MIT License - feel free to use for personal betting analysis.

## Disclaimer

This tool is for educational and analytical purposes. Always gamble responsibly.
