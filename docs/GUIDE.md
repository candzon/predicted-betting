# Understat Betting Analysis Scraper - COMPLETE GUIDE

A robust web scraper for Understat.com designed to feed betting analysis tools with accurate team statistics including Expected Goals (xG) metrics.

## ⚠️ IMPORTANT UPDATE - January 2026

**Understat.com now uses client-side rendering (JavaScript-based), making it impossible to scrape with simple HTTP requests.**

### Your Options:

1. **✅ RECOMMENDED: Use Selenium** (Browser automation - slower but works)
   ```bash
   pip install selenium
   ```
   Then set `USE_SELENIUM = True` in [main.py](main.py)

2. **🧪 Use Sample Data** (For testing database integration)
   - Default mode when Selenium is not installed
   - Generates mock data to test your betting models

3. **🔍 Manual Data Entry** (Copy from Understat website)
   - Visit https://understat.com/league/EPL/2024
   - Manually transcribe into the database

4. **💡 Alternative Data Sources**
   - Consider APIs like Football-Data.org, API-Football, etc.
   - May require paid subscriptions for xG data

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download this project
cd predicted-betting

# Install Python dependencies
pip install -r requirements.txt

# Generate Prisma client
prisma generate --schema=schema.prisma

# Create SQLite database
prisma db push --schema=schema.prisma
```

### 2. Choose Your Mode

#### Option A: Sample Data Mode (Default - No Setup Needed)
```bash
python main.py
```
This will populate the database with sample EPL data for testing.

#### Option B: Real Data with Selenium
```bash
# Install Selenium
pip install selenium

# Install ChromeDriver (required for Selenium)
# Windows: Download from https://chromedriver.chromium.org/
# Or use: pip install webdriver-manager
```

Then edit [main.py](main.py):
```python
USE_SELENIUM = True  # Change from False to True
```

Run the scraper:
```bash
python main.py
```

## 📁 Project Structure

```
predicted-betting/
├── schema.prisma              # Database schema (SQLite + TeamStats model)
├── understat_scraper.py       # Scraper class with Selenium support
├── main.py                    # Main orchestration script
├── db_utils.py                # Database query utilities
├── test_scraper.py            # Test suite
├── setup.py                   # Automated setup script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── betting_analysis.db        # SQLite database (generated)
```

## 📊 Database Schema

### TeamStats Model

| Field    | Type   | Description                          |
|----------|--------|--------------------------------------|
| id       | Int    | Auto-increment primary key           |
| league   | String | League name (EPL, La_liga, etc.)     |
| season   | Int    | Season year (2024, 2023, etc.)       |
| teamName | String | Team name                            |
| matches  | Int    | Total matches played                 |
| wins     | Int    | Wins                                 |
| draws    | Int    | Draws                                |
| loses    | Int    | Losses                               |
| scored   | Int    | Goals scored                         |
| missed   | Int    | Goals conceded                       |
| xG       | Float  | Expected Goals (KEY betting metric)  |
| xGA      | Float  | Expected Goals Against               |
| xPTS     | Float  | Expected Points                      |

**Unique Constraint**: `(teamName, league, season)` prevents duplicates

## 🎯 Usage Examples

### Query Database

```bash
# View summary
python db_utils.py summary 2024

# View league table
python db_utils.py table EPL 2024

# Find top xG teams
python db_utils.py top-xg 10 2024

# Find best defenses (lowest xGA)
python db_utils.py top-defense 10 2024

# Analyze value bets
python db_utils.py value-bets 2024
```

### Programmatic Access

```python
import asyncio
from prisma import Prisma

async def get_teams():
    db = Prisma()
    await db.connect()
    
    # Get all EPL teams
    teams = await db.teamstats.find_many(
        where={'league': 'EPL', 'season': 2024},
        order={'xPTS': 'desc'}
    )
    
    for team in teams:
        print(f"{team.teamName}: xG={team.xG:.2f}, xPTS={team.xPTS:.2f}")
    
    await db.disconnect()

asyncio.run(get_teams())
```

## 🔧 Configuration

Edit [main.py](main.py) to customize:

```python
# Leagues to scrape
LEAGUES = [
    "EPL",         # English Premier League
    "La_liga",     # Spanish La Liga
    "Serie_A",     # Italian Serie A
    "Bundesliga",  # German Bundesliga
    "Ligue_1",     # French Ligue 1
    "RFPL"         # Russian Premier League
]

# Target season
SEASON = 2024  # 2024 = 2024/2025 season

# Scraping mode
USE_SELENIUM = False  # Set to True for real scraping
```

## 📈 Betting Use Cases

The extracted xG metrics enable powerful betting strategies:

### 1. **Value Betting**
```python
python db_utils.py value-bets 2024
```
Identifies teams:
- **Underperforming**: Scoring less than xG suggests → Future goals likely
- **Overperforming**: Scoring more than xG suggests → Regression expected

### 2. **Expected Points Model**
xPTS indicates "true" team strength beyond luck. Compare with actual points to find:
- **Unlucky teams** (xPTS > actual points) → Good value
- **Lucky teams** (xPTS < actual points) → Avoid

### 3. **Over/Under Predictions**
```python
# Teams with high combined xG + xGA = high-scoring matches
SELECT teamName, (xG + xGA) / matches as total_xg_per_match
FROM TeamStats
WHERE season = 2024
ORDER BY total_xg_per_match DESC;
```

### 4. **Form Analysis**
Track xG trends over recent matches to identify:
- Improving teams (xG increasing)
- Declining teams (xG decreasing)

## 🛠️ Troubleshooting

### "Could not extract data from page source"

**Cause**: Understat uses client-side rendering.

**Solution**:
1. Install Selenium: `pip install selenium`
2. Set `USE_SELENIUM = True` in [main.py](main.py)
3. Run again

### "Selenium WebDriver not found"

**Solution**: Install ChromeDriver
```bash
# Windows
pip install webdriver-manager

# Or download manually from:
# https://chromedriver.chromium.org/
```

### "Prisma Client Not Found"

**Solution**:
```bash
prisma generate --schema=schema.prisma
```

### Database is Empty

**Check**:
1. Did `main.py` run successfully?
2. Check for errors in the output
3. Verify Selenium is working if enabled
4. Try sample data mode first (`USE_SELENIUM = False`)

## 🧪 Testing

Run the test suite:
```bash
python test_scraper.py
```

Tests verify:
- ✅ Database operations (upsert, query)
- ✅ Scraper functionality (if Selenium available)
- ✅ Data transformation

## 📦 Dependencies

```
requests>=2.31.0           # HTTP requests
beautifulsoup4>=4.12.0     # HTML parsing
lxml>=5.0.0                # XML/HTML parser
prisma>=0.11.0             # ORM for Python
selenium (optional)        # Browser automation for real scraping
```

## 🔐 Rate Limiting & Ethics

- **Respect robots.txt**: Check Understat's robots.txt
- **Add delays**: Use `time.sleep()` between requests
- **Limit requests**: Don't hammer the server
- **Use responsibly**: For personal analysis only

## 📜 License

MIT License - Free for personal betting analysis and educational purposes.

## ⚠️ Disclaimer

This tool is for **educational and analytical purposes only**.

- **Not financial advice**: Always do your own research
- **Gamble responsibly**: Only bet what you can afford to lose
- **Legal compliance**: Ensure betting is legal in your jurisdiction
- **No guarantees**: xG is predictive, not definitive

## 🆘 Support

### Common Questions

**Q: Can I scrape historical seasons?**
A: Yes! Change `SEASON = 2023` (or 2022, 2021, etc.) in [main.py](main.py)

**Q: How often should I update data?**
A: After each match week. Understat updates after matches are complete.

**Q: Can I export to Excel?**
A: Yes! The database utilities support CSV/XLSX export (see [db_utils.py](db_utils.py))

**Q: Does this work for other leagues?**
A: Yes! Understat covers EPL, La Liga, Serie A, Bundesliga, Ligue 1, and RFPL.

## 🚀 Next Steps

1. ✅ **Set up database**: `python main.py` (sample data mode)
2. 📊 **Explore data**: `python db_utils.py summary`
3. 🔧 **Install Selenium**: For real data scraping
4. 📈 **Build models**: Use xG data for betting predictions
5. 🎯 **Analyze value**: Find underperforming teams

## 🤝 Contributing

Have improvements? Found a bug? Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

**Made with ⚽ for betting enthusiasts**

*Last updated: January 2026*
