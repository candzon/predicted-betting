import asyncio
from prisma import Prisma

async def list_teams(league, season):
    db = Prisma()
    await db.connect()
    try:
        teams = await db.teamstats.find_many(where={'league': league, 'season': season})
        print(f"Found {len(teams)} teams for {league} {season}")
        for t in teams:
            print(repr(t.teamName))
    finally:
        await db.disconnect()

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print('Usage: python debug_team_lookup.py <League> <Season>')
    else:
        league = sys.argv[1]
        season = int(sys.argv[2])
        asyncio.run(list_teams(league, season))
