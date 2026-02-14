"""
Main Entry Point for Understat Betting Analysis Scraper
--------------------------------------------------------
Orchestrates data scraping and database operations using Prisma ORM.

IMPORTANT NOTES:
- Understat.com now uses client-side rendering
- For best results, install Selenium: pip install selenium
- Alternative: Use sample data for testing the database integration
"""

import asyncio
import logging
from typing import List
from prisma import Prisma
from src.understat_scraper import UnderstatScraper, get_sample_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
LEAGUES = [
    "EPL",         # English Premier League
    "La_liga",     # Spanish La Liga
    "Bundesliga", # German Bundesliga
    "Serie_A",     # Italian Serie A
    "Ligue_1",      # French Ligue 1
    "RFPL"         # Russian Premier League
]

SEASON = 2025  # Target season (use 2024 for current season data)

# Set this to True if you have Selenium installed
USE_SELENIUM = True  # Change to True after: pip install selenium


async def upsert_team_stats(db: Prisma, team_data: dict) -> None:
    """
    Upsert (update if exists, insert if new) team statistics.
    
    Args:
        db: Prisma database client
        team_data: Dictionary containing team statistics
    """
    try:
        await db.teamstats.upsert(
            where={
                'unique_team_season': {
                    'teamName': team_data['teamName'],
                    'league': team_data['league'],
                    'season': team_data['season']
                }
            },
            data={
                'create': team_data,
                'update': {
                    'matches': team_data['matches'],
                    'wins': team_data['wins'],
                    'draws': team_data['draws'],
                    'loses': team_data['loses'],
                    'scored': team_data['scored'],
                    'missed': team_data['missed'],
                    'xG': team_data['xG'],
                    'xGA': team_data['xGA'],
                    'xPTS': team_data['xPTS'],
                    # Form 10 Pertandingan Terakhir
                    'last10_form': team_data.get('last10_form', ''),
                    'last10_wins': team_data.get('last10_wins', 0),
                    'last10_draws': team_data.get('last10_draws', 0),
                    'last10_loses': team_data.get('last10_loses', 0),
                    'last10_points': team_data.get('last10_points', 0),
                    # Tren Over/Under 2.5
                    'last10_over': team_data.get('last10_over', 0),
                    'last10_under': team_data.get('last10_under', 0),
                    'last10_over_pct': team_data.get('last10_over_pct', 0.0),
                    # Home/Away Split
                    'home_wins': team_data.get('home_wins', 0),
                    'home_draws': team_data.get('home_draws', 0),
                    'home_loses': team_data.get('home_loses', 0),
                    'home_over': team_data.get('home_over', 0),
                    'away_wins': team_data.get('away_wins', 0),
                    'away_draws': team_data.get('away_draws', 0),
                    'away_loses': team_data.get('away_loses', 0),
                    'away_over': team_data.get('away_over', 0),
                }
            }
        )
    except Exception as e:
        logger.error(f"Error upserting {team_data['teamName']}: {e}")
        raise


async def scrape_and_store(league: str, season: int, scraper: UnderstatScraper, db: Prisma) -> int:
    """
    Scrape data for a league and store in database.
    
    Args:
        league: League name
        season: Season year
        scraper: UnderstatScraper instance (or None to use sample data)
        db: Prisma database client
        
    Returns:
        Number of teams successfully stored
    """
    try:
        # Fetch data from Understat
        logger.info(f"Scraping {league} {season}...")
        
        if scraper:
            teams_data = scraper.fetch_data(league, season)
        else:
            # Use sample data if no scraper provided
            logger.warning(f"Using sample data for {league} {season}")
            teams_data = get_sample_data(league, season)
        
        if not teams_data:
            logger.warning(f"No data available for {league} {season}")
            return 0
        
        # Store each team in database
        stored_count = 0
        for team_data in teams_data:
            try:
                await upsert_team_stats(db, team_data)
                stored_count += 1
            except Exception as e:
                logger.warning(f"Failed to store {team_data.get('teamName', 'Unknown')}: {e}")
        
        logger.info(f"✓ Scraped {stored_count} teams for {league} {season}")
        return stored_count
        
    except Exception as e:
        logger.error(f"✗ Failed to scrape {league} {season}: {e}")
        return 0


async def main():
    """
    Main execution function.
    
    Initializes Prisma, scrapes configured leagues, and stores data.
    """
    print("\n" + "="*70)
    print("UNDERSTAT BETTING ANALYSIS SCRAPER")
    print("="*70)
    
    # Check Selenium status
    use_selenium_mode = USE_SELENIUM
    if use_selenium_mode:
        print("✓ Selenium mode ENABLED - will attempt real scraping")
        try:
            import selenium
            print("✓ Selenium package found")
        except ImportError:
            print("✗ Selenium not installed! Install with: pip install selenium")
            print("  Falling back to sample data mode")
            use_selenium_mode = False
    else:
        print("⚠ Selenium mode DISABLED - using sample data")
        print("  To enable real scraping:")
        print("  1. Install Selenium: pip install selenium")
        print("  2. Set USE_SELENIUM = True in main.py")
    
    print("="*70 + "\n")
    
    # Initialize Prisma database
    db = Prisma()
    await db.connect()
    logger.info("Connected to database")
    
    # Initialize scraper (or None for sample data)
    scraper = None
    if use_selenium_mode:
        scraper = UnderstatScraper(timeout=30, use_selenium=True)
    
    try:
        total_teams = 0
        successful_leagues = 0
        
        # For demo purposes, just scrape EPL if using sample data
        leagues_to_process = LEAGUES if use_selenium_mode else ["EPL"]
        
        # Process each league
        for league in leagues_to_process:
            try:
                count = await scrape_and_store(league, SEASON, scraper, db)
                total_teams += count
                if count > 0:
                    successful_leagues += 1
            except Exception as e:
                logger.error(f"Error processing {league}: {e}")
        
        # Summary
        print("\n" + "="*70)
        print("SCRAPING SUMMARY")
        print("="*70)
        print(f"Mode: {'SELENIUM (Real Data)' if use_selenium_mode else 'SAMPLE DATA'}")
        print(f"Season: {SEASON}")
        print(f"Leagues processed: {successful_leagues}/{len(leagues_to_process)}")
        print(f"Total teams stored: {total_teams}")
        print("="*70)
        
        # Display sample data
        if total_teams > 0:
            print("\nSample data from database:")
            sample = await db.teamstats.find_first(
                where={'season': SEASON},
                order={'xG': 'desc'}
            )
            if sample:
                print(f"\nTop xG Team: {sample.teamName} ({sample.league})")
                print(f"  Matches: {sample.matches}")
                print(f"  xG: {sample.xG:.2f} | xGA: {sample.xGA:.2f} | xPTS: {sample.xPTS:.2f}")
                print(f"  Record: {sample.wins}W-{sample.draws}D-{sample.loses}L")
                print(f"  Goals: {sample.scored} scored, {sample.missed} conceded")
        
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)
        if not use_selenium_mode:
            print("✓ Database setup verified with sample data")
            print("\nTo get real Understat data:")
            print("  1. pip install selenium")
            print("  2. Set USE_SELENIUM = True in main.py")
            print("  3. Run: python main.py")
        else:
            print("✓ Real data scraping complete!")
        
        print("\nQuery your data:")
        print("  python db_utils.py summary")
        print("  python db_utils.py table EPL")
        print("  python db_utils.py value-bets")
        print("="*70 + "\n")
        
    finally:
        # Cleanup
        if scraper:
            scraper.close()
        await db.disconnect()
        logger.info("Disconnected from database")


async def scrape_single_league(league: str, season: int):
    """
    Utility function to scrape a single league.
    
    Args:
        league: League name (e.g., "EPL")
        season: Season year (e.g., 2025)
    """
    db = Prisma()
    await db.connect()
    
    scraper = UnderstatScraper()
    
    try:
        count = await scrape_and_store(league, season, scraper, db)
        print(f"\nSuccessfully scraped {count} teams for {league} {season}")
    finally:
        scraper.close()
        await db.disconnect()


if __name__ == "__main__":
    # Run the main scraper
    asyncio.run(main())
    
    # Example: To scrape a single league, uncomment below:
    # asyncio.run(scrape_single_league("EPL", 2025))
