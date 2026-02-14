"""
Database Utilities for Understat Betting Analysis
--------------------------------------------------
Helpful functions for querying and managing the betting database.
"""

import asyncio
from typing import List, Optional
from prisma import Prisma
from prisma.models import TeamStats


async def get_league_standings(league: str, season: int) -> List[TeamStats]:
    """
    Get league standings sorted by xPTS (Expected Points).
    
    Args:
        league: League name (e.g., "EPL")
        season: Season year
        
    Returns:
        List of TeamStats ordered by xPTS descending
    """
    db = Prisma()
    await db.connect()
    
    try:
        teams = await db.teamstats.find_many(
            where={
                'league': league,
                'season': season
            },
            order={'xPTS': 'desc'}
        )
        return teams
    finally:
        await db.disconnect()


async def get_top_xg_teams(limit: int = 10, season: int = 2025) -> List[TeamStats]:
    """
    Get teams with highest Expected Goals across all leagues.
    
    Args:
        limit: Number of teams to return
        season: Season year
        
    Returns:
        List of top xG teams
    """
    db = Prisma()
    await db.connect()
    
    try:
        teams = await db.teamstats.find_many(
            where={'season': season},
            order={'xG': 'desc'},
            take=limit
        )
        return teams
    finally:
        await db.disconnect()


async def get_defensive_teams(limit: int = 10, season: int = 2025) -> List[TeamStats]:
    """
    Get teams with lowest xGA (best defenses).
    
    Args:
        limit: Number of teams to return
        season: Season year
        
    Returns:
        List of best defensive teams
    """
    db = Prisma()
    await db.connect()
    
    try:
        teams = await db.teamstats.find_many(
            where={'season': season},
            order={'xGA': 'asc'},
            take=limit
        )
        return teams
    finally:
        await db.disconnect()


async def find_value_bets(season: int = 2025, xg_threshold: float = 2.0):
    """
    Find potential value bets where xG significantly differs from actual goals.
    
    Teams scoring fewer goals than xG suggests = underperforming (value for over bets)
    Teams scoring more goals than xG suggests = overperforming (value for under bets)
    
    Args:
        season: Season year
        xg_threshold: Minimum difference threshold
        
    Returns:
        Dictionary with underperforming and overperforming teams
    """
    db = Prisma()
    await db.connect()
    
    try:
        all_teams = await db.teamstats.find_many(
            where={'season': season}
        )
        
        underperforming = []
        overperforming = []
        
        for team in all_teams:
            if team.matches == 0:
                continue
                
            xg_per_match = team.xG / team.matches
            actual_per_match = team.scored / team.matches
            diff = xg_per_match - actual_per_match
            
            if abs(diff) >= xg_threshold:
                team_info = {
                    'team': team.teamName,
                    'league': team.league,
                    'xG_per_match': round(xg_per_match, 2),
                    'actual_per_match': round(actual_per_match, 2),
                    'difference': round(diff, 2)
                }
                
                if diff > 0:
                    underperforming.append(team_info)
                else:
                    overperforming.append(team_info)
        
        return {
            'underperforming': sorted(underperforming, key=lambda x: x['difference'], reverse=True),
            'overperforming': sorted(overperforming, key=lambda x: x['difference'])
        }
    finally:
        await db.disconnect()


async def display_league_table(league: str, season: int):
    """
    Display a formatted league table with betting metrics.
    
    Args:
        league: League name
        season: Season year
    """
    teams = await get_league_standings(league, season)
    
    if not teams:
        print(f"No data found for {league} {season}")
        return
    
    print(f"\n{'='*100}")
    print(f"{league} {season} - Expected Points Table")
    print(f"{'='*100}")
    print(f"{'Pos':<4} {'Team':<25} {'M':<4} {'W-D-L':<8} {'GF-GA':<8} {'xG':<6} {'xGA':<6} {'xPTS':<6}")
    print(f"{'-'*100}")
    
    for idx, team in enumerate(teams, 1):
        record = f"{team.wins}-{team.draws}-{team.loses}"
        goals = f"{team.scored}-{team.missed}"
        
        print(f"{idx:<4} {team.teamName:<25} {team.matches:<4} {record:<8} {goals:<8} "
              f"{team.xG:<6.1f} {team.xGA:<6.1f} {team.xPTS:<6.1f}")
    
    print(f"{'='*100}\n")


async def get_stats_summary(season: int = 2025):
    """
    Get summary statistics for the season.
    
    Args:
        season: Season year
    """
    db = Prisma()
    await db.connect()
    
    try:
        total_teams = await db.teamstats.count(where={'season': season})
        
        if total_teams == 0:
            print(f"No data for season {season}")
            return
        
        leagues = await db.teamstats.find_many(
            where={'season': season},
            distinct=['league']
        )
        
        print(f"\n{'='*60}")
        print(f"DATABASE SUMMARY - Season {season}")
        print(f"{'='*60}")
        print(f"Total Teams: {total_teams}")
        print(f"Leagues: {len(leagues)}")
        print(f"League breakdown:")
        
        for league_item in leagues:
            count = await db.teamstats.count(
                where={'season': season, 'league': league_item.league}
            )
            print(f"  - {league_item.league}: {count} teams")
        
        print(f"{'='*60}\n")
        
    finally:
        await db.disconnect()


# CLI Interface
async def main():
    """Interactive CLI for database queries."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python db_utils.py summary [season]")
        print("  python db_utils.py table <league> [season]")
        print("  python db_utils.py top-xg [limit] [season]")
        print("  python db_utils.py top-defense [limit] [season]")
        print("  python db_utils.py value-bets [season]")
        return
    
    command = sys.argv[1]
    season = int(sys.argv[-1]) if len(sys.argv) > 2 and sys.argv[-1].isdigit() else 2025
    
    if command == "summary":
        await get_stats_summary(season)
    
    elif command == "table" and len(sys.argv) >= 3:
        league = sys.argv[2]
        await display_league_table(league, season)
    
    elif command == "top-xg":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        teams = await get_top_xg_teams(limit, season)
        print(f"\nTop {limit} xG Teams - Season {season}")
        print(f"{'='*80}")
        for idx, team in enumerate(teams, 1):
            print(f"{idx}. {team.teamName} ({team.league}) - xG: {team.xG:.2f}")
    
    elif command == "top-defense":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        teams = await get_defensive_teams(limit, season)
        print(f"\nTop {limit} Defensive Teams - Season {season}")
        print(f"{'='*80}")
        for idx, team in enumerate(teams, 1):
            print(f"{idx}. {team.teamName} ({team.league}) - xGA: {team.xGA:.2f}")
    
    elif command == "value-bets":
        results = await find_value_bets(season)
        
        print(f"\n{'='*80}")
        print(f"VALUE BET ANALYSIS - Season {season}")
        print(f"{'='*80}")
        
        print("\nUNDERPERFORMING (Scoring less than xG suggests):")
        print(f"{'Team':<25} {'League':<12} {'xG/match':<10} {'Actual':<10} {'Diff':<8}")
        print(f"{'-'*80}")
        for team in results['underperforming'][:10]:
            print(f"{team['team']:<25} {team['league']:<12} {team['xG_per_match']:<10} "
                  f"{team['actual_per_match']:<10} +{team['difference']:<8}")
        
        print("\nOVERPERFORMING (Scoring more than xG suggests):")
        print(f"{'Team':<25} {'League':<12} {'xG/match':<10} {'Actual':<10} {'Diff':<8}")
        print(f"{'-'*80}")
        for team in results['overperforming'][:10]:
            print(f"{team['team']:<25} {team['league']:<12} {team['xG_per_match']:<10} "
                  f"{team['actual_per_match']:<10} {team['difference']:<8}")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
