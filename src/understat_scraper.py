"""
Understat.com Web Scraper - UPDATED VERSION
--------------------------------------------
Extracts betting metrics from Understat. 
IMPORTANT NOTE: Understat has moved to client-side rendering, making it difficult
to scrape without Selenium. This version provides a working foundation with fallback options.

OPTIONS FOR USERS:
1. Use Selenium (recommended for production - install: pip install selenium)
2. Use this requests-based version with the understanding that it may require updates
3. Consider using Understat's unofficial API if available

This implementation attempts to extract data from script tags, but may need
updates based on Understat's current structure.
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnderstatScraper:
    """
    Scraper for Understat.com league statistics.
    
    NOTE: Understat uses client-side rendering. This scraper attempts to extract
    data from embedded JSON in the page source. If this fails, consider:
    1. Using Selenium for browser automation
    2. Finding Understat's API endpoints
    3. Using alternative data sources
    """
    
    BASE_URL = "https://understat.com/league"
    
    def __init__(self, timeout: int = 30, use_selenium: bool = False):
        """
        Initialize the scraper.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
            use_selenium: Use Selenium WebDriver (requires selenium package)
        """
        self.timeout = timeout
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://understat.com/'
        })
        
        if use_selenium:
            self._init_selenium()
    
    def _init_selenium(self):
        """Initialize Selenium WebDriver if requested."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument(f'user-agent={self.session.headers["User-Agent"]}')
            
            self.driver = webdriver.Chrome(options=options)
            logger.info("Selenium WebDriver initialized")
        except ImportError:
            logger.warning("Selenium not installed. Install with: pip install selenium")
            self.use_selenium = False
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False
    
    def fetch_data(self, league: str, season: int) -> List[Dict]:
        """
        Fetch team statistics for a given league and season.
        
        Args:
            league: League name (e.g., "EPL")
            season: Season year (e.g., 2025, 2024)
        
        Returns:
            List of dictionaries containing team statistics
        """
        if self.use_selenium:
            return self._fetch_with_selenium(league, season)
        else:
            return self._fetch_with_requests(league, season)
    
    def _fetch_with_selenium(self, league: str, season: int) -> List[Dict]:
        """Fetch data using Selenium (RECOMMENDED for Understat)."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        url = f"{self.BASE_URL}/{league}/{season}"
        logger.info(f"Fetching with Selenium: {url}")
        
        try:
            self.driver.get(url)
            
            # Wait for the table to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "chemp"))
            )
            
            # Give extra time for JavaScript to populate data
            time.sleep(2)
            
            # Get page source after JavaScript execution
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Extract data from the loaded page
            return self._extract_from_rendered_page(soup, league, season)
            
        except Exception as e:
            logger.error(f"Selenium fetch failed: {e}")
            raise
    
    def _fetch_with_requests(self, league: str, season: int) -> List[Dict]:
        """
        Fetch data using requests (LIMITED - may not work due to client-side rendering).
        
        This method provides sample/mock data for demonstration purposes.
        For production use, consider using Selenium or finding API endpoints.
        """
        url = f"{self.BASE_URL}/{league}/{season}"
        logger.info(f"Fetching data from: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try to extract from scripts
            data = self._try_extract_from_scripts(soup, league, season)
            
            if data:
                return data
            
            # If extraction fails, provide helpful error message
            logger.warning(
                "Could not extract data from page source. "
                "Understat likely uses client-side rendering."
            )
            logger.warning(
                "SOLUTION: Set use_selenium=True when creating UnderstatScraper, "
                "or manually provide data, or use alternative data sources."
            )
            
            # Return empty list instead of raising error
            # This allows the rest of the code to work with manual data entry
            return []
            
        except requests.RequestException as e:
            logger.error(f"HTTP request failed for {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing {league} {season}: {e}")
            raise
    
    def _try_extract_from_scripts(self, soup: BeautifulSoup, league: str, season: int) -> List[Dict]:
        """
        Attempt to extract data from script tags.
        This method tries various patterns to find embedded JSON data.
        """
        scripts = soup.find_all('script')
        
        for script in scripts:
            if not script.string:
                continue
            
            # Try multiple patterns
            patterns = [
                r"var\s+teamsData\s*=\s*JSON\.parse\('(.+?)'\)",
                r"teamsData\s*:\s*JSON\.parse\('(.+?)'\)",
                r"data\s*:\s*(\[.+?\])",
            ]
            
            for pattern in patterns:
                match = re.search(pattern, script.string, re.DOTALL)
                if match:
                    try:
                        encoded_string = match.group(1)
                        decoded = self._decode_unicode_escapes(encoded_string)
                        data = json.loads(decoded)
                        
                        if isinstance(data, list) and len(data) > 0:
                            logger.info(f"Found data using pattern: {pattern[:30]}...")
                            return self._transform_team_data(data, league, season)
                    except:
                        continue
        
        return None
    
    def _fetch_team_fixtures(self, team_name: str, team_id: str, league: str, season: int) -> List[Dict]:
        """
        Fetch match fixtures for a specific team from their individual page.
        This is necessary because match history is not available in the league table.
        
        Note: Understat renders match data in HTML elements (div.calendar-game)
        rather than in JavaScript variables, so we parse the HTML directly.
        """
        if not self.use_selenium or not hasattr(self, 'driver'):
            return []
        
        try:
            # Construct team URL (convert team name to URL format)
            team_url_name = team_name.replace(' ', '_')
            url = f"https://understat.com/team/{team_url_name}/{season}"
            
            logger.info(f"Fetching fixtures for {team_name} from {url}")
            self.driver.get(url)
            time.sleep(3)  # Wait for JavaScript to load
            
            soup = BeautifulSoup(self.driver.page_source, 'lxml')
            
            # Look for calendar-game divs (this is where match data is rendered)
            game_divs = soup.find_all('div', class_='calendar-game')
            
            if not game_divs:
                logger.warning(f"No calendar-game divs found for {team_name}")
                return []
            
            logger.info(f"Found {len(game_divs)} matches for {team_name}")
            
            fixtures = []
            for game_div in game_divs:
                try:
                    match_info = game_div.find('a', class_='match-info')
                    if not match_info:
                        continue
                    
                    # Check if result is available (finished match)
                    is_result = match_info.get('data-isresult') == 'true'
                    if not is_result:
                        continue  # Skip upcoming fixtures
                    
                    # Get opponent
                    opponent_link = game_div.find('div', class_='team-title')
                    if not opponent_link or not opponent_link.find('a'):
                        continue
                    opponent = opponent_link.find('a').get_text(strip=True)
                    
                    # Determine home/away
                    teams_goals = match_info.find('div', class_='teams-goals')
                    if not teams_goals:
                        continue
                    
                    goals_home = teams_goals.find('span', class_='team-home')
                    goals_away = teams_goals.find('span', class_='team-away')
                    
                    if not goals_home or not goals_away:
                        continue
                    
                    # Check which span has the data-win attribute
                    # This tells us which position our team was in
                    has_data_win_home = goals_home.has_attr('data-win')
                    has_data_win_away = goals_away.has_attr('data-win')
                    
                    # Parse goals
                    try:
                        goals_home_val = int(goals_home.get_text(strip=True))
                        goals_away_val = int(goals_away.get_text(strip=True))
                    except (ValueError, AttributeError):
                        continue
                    
                    # Get xG data if available
                    teams_xg = match_info.find('div', class_='teams-xG')
                    xg_home = None
                    xg_away = None
                    if teams_xg:
                        xg_home_elem = teams_xg.find('span', class_='team-home')
                        xg_away_elem = teams_xg.find('span', class_='team-away')
                        if xg_home_elem:
                            xg_text = xg_home_elem.get_text(strip=True).replace('\n', '')
                            try:
                                xg_home = float(xg_text)
                            except ValueError:
                                pass
                        if xg_away_elem:
                            xg_text = xg_away_elem.get_text(strip=True).replace('\n', '')
                            try:
                                xg_away = float(xg_text)
                            except ValueError:
                                pass
                    
                    # Extract match ID from href
                    match_href = match_info.get('href', '')
                    match_id = match_href.split('/')[-1] if '/' in match_href else None
                    
                    # Create fixture entry with raw data and data-win indicators
                    fixture = {
                        'id': match_id,
                        'opponent': opponent,
                        '_raw_home_goals': goals_home_val,
                        '_raw_away_goals': goals_away_val,
                        '_raw_xg_home': xg_home,
                        '_raw_xg_away': xg_away,
                        '_data_win_home': has_data_win_home,
                        '_data_win_away': has_data_win_away,
                    }
                    fixtures.append(fixture)
                    
                except Exception as e:
                    logger.warning(f"Error parsing game div: {e}")
                    continue
            
            if fixtures:
                logger.info(f"✓ Extracted {len(fixtures)} completed fixtures for {team_name}")
                return self._parse_fixtures_from_html(fixtures, team_name)
            else:
                logger.warning(f"No completed fixtures found for {team_name}")
                return []
            
        except Exception as e:
            logger.warning(f"Error fetching fixtures for {team_name}: {e}")
            return []
    
    def _parse_fixtures(self, fixtures: List[Dict], team_name: str) -> List[Dict]:
        """
        Parse raw fixture data into standardized match history format.
        """
        parsed_matches = []
        
        for fixture in fixtures:
            try:
                # Determine if home or away
                home_team = fixture.get('h', {}).get('title', '')
                away_team = fixture.get('a', {}).get('title', '')
                
                is_home = (home_team == team_name)
                
                # Get goals
                home_goals = int(fixture.get('goals', {}).get('h', 0))
                away_goals = int(fixture.get('goals', {}).get('a', 0))
                
                # Team's perspective
                if is_home:
                    goals_for = home_goals
                    goals_against = away_goals
                else:
                    goals_for = away_goals
                    goals_against = home_goals
                
                parsed_matches.append({
                    'isHome': is_home,
                    'goals': goals_for,
                    'against': goals_against,
                    'date': fixture.get('datetime', ''),
                })
                
            except Exception as e:
                logger.debug(f"Error parsing fixture: {e}")
                continue
        
        return parsed_matches
    
    def _parse_fixtures_from_html(self, fixtures: List[Dict], team_name: str) -> List[Dict]:
        """
        Parse fixture data extracted from HTML calendar-game divs.
        
        The calendar-game structure shows matches from the team's perspective:
        - team-home/team-away spans show the scores
        - The `data-win` attribute appears on the span of OUR team's position
        - If data-win is on team-home → we were HOME
        - If data-win is on team-away → we were AWAY
        - opponent name is shown below in team-title div
        """
        parsed_matches = []
        
        for fixture in fixtures:
            try:
                home_goals = fixture.get('_raw_home_goals', 0)
                away_goals = fixture.get('_raw_away_goals', 0)
                has_data_win_home = fixture.get('_data_win_home', False)
                has_data_win_away = fixture.get('_data_win_away', False)
                
                # Determine if our team was home or away based on where data-win appears
                if has_data_win_home:
                    # data-win on team-home → we were home
                    is_home = True
                    goals_for = home_goals
                    goals_against = away_goals
                elif has_data_win_away:
                    # data-win on team-away → we were away
                    is_home = False
                    goals_for = away_goals
                    goals_against = home_goals
                else:
                    # No data-win attribute (shouldn't happen for completed matches)
                    # Default assumption: if no indicator, skip
                    logger.debug(f"No data-win indicator for match {fixture.get('id')}, skipping")
                    continue
                
                parsed_matches.append({
                    'isHome': is_home,
                    'goals': goals_for,
                    'against': goals_against,
                    'opponent': fixture.get('opponent', ''),
                })
                
            except Exception as e:
                logger.debug(f"Error parsing HTML fixture: {e}")
                continue
        
        return parsed_matches
    
    def _extract_from_rendered_page(self, soup: BeautifulSoup, league: str, season: int) -> List[Dict]:
        """
        Extract data from a fully rendered page (used with Selenium).
        Parses the HTML table that was populated by JavaScript.
        Now also fetches individual team fixtures for match history.
        """
        try:
            # Try to find scripts with JSON data first
            scripts = soup.find_all('script')
            for script in scripts:
                if not script.string:
                    continue
                
                # Look for teamsData variable
                if 'var teamsData' in script.string or 'var datesData' in script.string:
                    # Try to extract JSON.parse data
                    match = re.search(r"var\s+teamsData\s*=\s*JSON\.parse\('(.+?)'\)", script.string, re.DOTALL)
                    if match:
                        try:
                            encoded_string = match.group(1)
                            decoded = self._decode_unicode_escapes(encoded_string)
                            data = json.loads(decoded)
                            
                            if isinstance(data, list) and len(data) > 0:
                                logger.info(f"Found teamsData in rendered page: {len(data)} teams")
                                
                                # Enhance each team with fixture data
                                for team in data:
                                    team_name = team.get('title', team.get('team', ''))
                                    team_id = team.get('id', '')
                                    
                                    if team_name:
                                        logger.info(f"Fetching fixtures for {team_name}...")
                                        fixtures = self._fetch_team_fixtures(team_name, team_id, league, season)
                                        if fixtures:
                                            team['history'] = fixtures
                                
                                return self._transform_team_data(data, league, season)
                        except Exception as e:
                            logger.debug(f"Failed to parse teamsData: {e}")
            
            # If script extraction failed, parse the rendered HTML table
            # Look for the table body containing team data
            tbody = soup.find('tbody')
            
            if tbody:
                team_rows = tbody.find_all('tr')
                
                if team_rows:
                    logger.info(f"Found {len(team_rows)} team rows in HTML table")
                    # Parse the rows
                    teams_data = []
                    for row in team_rows:
                        team_data = self._parse_table_row(row, league, season)
                        if team_data:
                            teams_data.append(team_data)
                    
                    if teams_data:
                        logger.info(f"Successfully extracted {len(teams_data)} teams from table")
                        
                        # Now fetch fixtures for each team
                        for i, team in enumerate(teams_data, 1):
                            team_name = team.get('teamName', '')
                            logger.info(f"[{i}/{len(teams_data)}] Processing {team_name}...")
                            if team_name:
                                fixtures = self._fetch_team_fixtures(team_name, '', league, season)
                                if fixtures:
                                    team['history'] = fixtures
                                    logger.info(f"  ✓ Added {len(fixtures)} fixtures to {team_name}")
                                else:
                                    logger.warning(f"  ✗ No fixtures for {team_name}")
                        
                        return self._transform_team_data(teams_data, league, season)
            
            logger.warning("Could not extract data from rendered page")
            
            # Save HTML for debugging only if no data found
            with open('rendered_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(str(soup.prettify()))
            logger.info("Saved rendered HTML to rendered_page_debug.html for inspection")
            
            return []
            
        except Exception as e:
            logger.error(f"Error extracting from rendered page: {e}")
            return []
    
    def _parse_table_row(self, row_element, league: str, season: int) -> Optional[Dict]:
        """
        Parse a single team row from HTML table.
        Expected structure: <tr> containing <td> elements with team stats.
        """
        try:
            cells = row_element.find_all('td')
            
            if len(cells) < 12:  # Need at least 12 cells for all our data
                return None
            
            # Extract team name from link
            team_link = cells[1].find('a')
            if not team_link:
                return None
            
            team_name = team_link.get_text(strip=True)
            
            # Extract numeric values (remove any sup/sub tags and clean text)
            def get_number(cell, is_float=False):
                try:
                    # For cells with nowrap class (xG, xGA, xPTS), extract text before <sup>
                    if 'nowrap' in cell.get('class', []):
                        # Get all text nodes, excluding sup/sub tags
                        text = ''
                        for content in cell.children:
                            if content.name not in ['sup', 'sub']:
                                if hasattr(content, 'strip'):
                                    text += content.strip()
                        text = text.strip()
                    else:
                        text = cell.get_text(strip=True)
                    
                    # Remove anything after space or newline (like +/- indicators)
                    text = text.split('\n')[0].split(' ')[0]
                    return float(text) if is_float else int(text)
                except Exception as e:
                    logger.debug(f"Error parsing number from cell: {e}")
                    return 0.0 if is_float else 0
            
            team_stats = {
                'league': league,
                'season': season,
                'teamName': team_name,
                'matches': get_number(cells[2]),      # M (matches)
                'wins': get_number(cells[3]),         # W (wins)
                'draws': get_number(cells[4]),        # D (draws)
                'loses': get_number(cells[5]),        # L (loses)
                'scored': get_number(cells[6]),       # GF (goals for/scored)
                'missed': get_number(cells[7]),       # GA (goals against/missed)
                'xG': get_number(cells[9], True),     # xG (Expected Goals)
                'xGA': get_number(cells[10], True),   # xGA (Expected Goals Against)
                'xPTS': get_number(cells[11], True)   # xPTS (Expected Points)
            }
            
            logger.debug(f"Parsed team: {team_name} - xG:{team_stats['xG']:.2f}, xPTS:{team_stats['xPTS']:.2f}")
            return team_stats
            
        except Exception as e:
            logger.debug(f"Error parsing table row: {e}")
            return None
    
    def _decode_unicode_escapes(self, encoded_string: str) -> str:
        """Decode unicode escape sequences."""
        try:
            decoded = encoded_string.encode('utf-8').decode('unicode_escape')
            return decoded
        except:
            return encoded_string
    
    def _transform_team_data(self, raw_data: List[Dict], league: str, season: int) -> List[Dict]:
        """Transform raw scraped data to match our database schema."""
        transformed_data = []
        
        for team in raw_data:
            try:
                team_stats = {
                    'league': league,
                    'season': season,
                    'teamName': team.get('teamName', team.get('title', team.get('team', team.get('name', 'Unknown')))),
                    'matches': int(team.get('matches', team.get('games', 0))),
                    'wins': int(team.get('wins', team.get('w', 0))),
                    'draws': int(team.get('draws', team.get('d', 0))),
                    'loses': int(team.get('loses', team.get('losses', team.get('l', 0)))),
                    'scored': int(team.get('scored', team.get('goals_for', team.get('gf', 0)))),
                    'missed': int(team.get('missed', team.get('conceded', team.get('goals_against', team.get('ga', 0))))),
                    'xG': float(team.get('xG', team.get('expected_goals', 0.0))),
                    'xGA': float(team.get('xGA', team.get('expected_goals_against', 0.0))),
                    'xPTS': float(team.get('xpts', team.get('xPTS', team.get('expected_points', 0.0))))
                }
                # Compute recent-match and home/away breakdown if possible
                try:
                    recent_stats = self._compute_recent_stats(team)
                    team_stats.update(recent_stats)
                except Exception:
                    # Non-fatal: if we can't compute recent stats, continue without them
                    pass
                transformed_data.append(team_stats)
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping team due to data error: {e}")
                continue
        
        return transformed_data
    
    def close(self):
        """Close the session and driver."""
        self.session.close()
        if self.use_selenium and hasattr(self, 'driver'):
            self.driver.quit()

    def _compute_recent_stats(self, team_raw: Dict) -> Dict:
        """
        Compute advanced statistics from team's match history:
        - Last 10 matches form (W/D/L string and points)
        - Home/Away split statistics  
        - Over/Under 2.5 goals trends and percentages
        
        Args:
            team_raw: Raw team data containing match history
            
        Returns:
            Dictionary with computed statistics including:
            - last10_form: String like "WWDLWWDWWL"
            - last10_points: Total points from last 10 matches
            - last10_over_pct: Percentage of Over 2.5 matches
            - Home/Away W/D/L splits
        """
        # Try several possible fields that may contain per-match data
        possible_lists = [
            team_raw.get('history'),
            team_raw.get('matches'),
            team_raw.get('recent'),
            team_raw.get('last_matches'),
            team_raw.get('last10'),
        ]

        matches_list = None
        for candidate in possible_lists:
            if isinstance(candidate, list) and len(candidate) > 0:
                matches_list = candidate
                break

        # Default stats if no history available
        if not matches_list:
            return {
                'last10_form': '',
                'last10_wins': 0,
                'last10_draws': 0,
                'last10_loses': 0,
                'last10_points': 0,
                'last10_over': 0,
                'last10_under': 0,
                'last10_over_pct': 0.0,
                'home_wins': 0,
                'home_draws': 0,
                'home_loses': 0,
                'away_wins': 0,
                'away_draws': 0,
                'away_loses': 0,
                'home_over': 0,
                'away_over': 0,
            }

        # We'll consider the last up-to-10 matches (assume chronological order)
        tail = matches_list[-10:]

        # Initialize counters
        form = []
        last10_wins = 0
        last10_draws = 0
        last10_loses = 0
        last10_points = 0
        last10_over = 0
        last10_under = 0
        
        home_wins = away_wins = 0
        home_draws = away_draws = 0
        home_loses = away_loses = 0
        home_over = away_over = 0

        for m in tail:
            # Determine home/away for the team
            is_home = None
            if isinstance(m, dict):
                # Common keys
                if 'isHome' in m:
                    is_home = bool(m.get('isHome'))
                elif 'h_a' in m:
                    is_home = (m.get('h_a') == 'h')
                elif 'side' in m:
                    is_home = (m.get('side') == 'h')
                elif 'home' in m and isinstance(m.get('home'), bool):
                    is_home = bool(m.get('home'))

                # Extract goals for/against with flexible keys
                def parse_goal(key_variants):
                    for k in key_variants:
                        if k in m:
                            try:
                                return int(m.get(k))
                            except Exception:
                                try:
                                    return int(float(m.get(k)))
                                except Exception:
                                    continue
                    return None

                gf = parse_goal(['goals', 'goalsFor', 'goals_for', 'team_goals', 'scored'])
                ga = parse_goal(['against', 'goalsAgainst', 'goals_against', 'opp_goals', 'conceded'])

                # Some feeds include separate home/away goal fields
                if gf is None or ga is None:
                    # try to infer from home/away specific keys
                    if is_home is True:
                        gf = gf or parse_goal(['home_goals', 'goals_home', 'hg'])
                        ga = ga or parse_goal(['away_goals', 'goals_away', 'ag'])
                    elif is_home is False:
                        gf = gf or parse_goal(['away_goals', 'goals_away', 'ag'])
                        ga = ga or parse_goal(['home_goals', 'goals_home', 'hg'])

            else:
                # Not a dict — skip
                continue

            # If we still can't parse scores, skip this match
            if gf is None or ga is None or is_home is None:
                continue

            # Determine result and points
            if gf > ga:
                res = 'W'
                points = 3
                last10_wins += 1
                if is_home:
                    home_wins += 1
                else:
                    away_wins += 1
            elif gf == ga:
                res = 'D'
                points = 1
                last10_draws += 1
                if is_home:
                    home_draws += 1
                else:
                    away_draws += 1
            else:
                res = 'L'
                points = 0
                last10_loses += 1
                if is_home:
                    home_loses += 1
                else:
                    away_loses += 1

            form.append(res)
            last10_points += points

            # Over 2.5 goals check (total >= 3)
            total_goals = gf + ga
            if total_goals >= 3:
                last10_over += 1
                if is_home:
                    home_over += 1
                else:
                    away_over += 1
            else:
                last10_under += 1
        
        # Calculate Over 2.5 percentage
        total_matches = len(form)
        last10_over_pct = (last10_over / total_matches * 100) if total_matches > 0 else 0.0

        return {
            'last10_form': ''.join(form),  # e.g., "WWDLWWDWWL"
            'last10_wins': last10_wins,
            'last10_draws': last10_draws,
            'last10_loses': last10_loses,
            'last10_points': last10_points,
            'last10_over': last10_over,
            'last10_under': last10_under,
            'last10_over_pct': round(last10_over_pct, 2),
            'home_wins': home_wins,
            'home_draws': home_draws,
            'home_loses': home_loses,
            'away_wins': away_wins,
            'away_draws': away_draws,
            'away_loses': away_loses,
            'home_over': home_over,
            'away_over': away_over,
        }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Sample data for testing/demonstration
def get_sample_data(league: str = "EPL", season: int = 2024) -> List[Dict]:
    """
    Provides sample data for testing when web scraping isn't working.
    
    NOTE: This is mock data for demonstration. For real data:
    1. Use Selenium: UnderstatScraper(use_selenium=True)
    2. Manual entry from Understat website
    3. Alternative data sources
    """
    logger.warning("Using sample/mock data - not real Understat data!")
    
    sample_teams = [
        {
            "teamName": "Manchester City",
            "matches": 20,
            "wins": 14,
            "draws": 4,
            "loses": 2,
            "scored": 45,
            "missed": 18,
            "xG": 48.5,
            "xGA": 19.2,
            "xPTS": 48.3,
            "history": [
                {"isHome": True, "goals": 3, "against": 1},   # W, Over (H)
                {"isHome": False, "goals": 2, "against": 0},  # W, Under (A)
                {"isHome": True, "goals": 2, "against": 2},   # D, Over (H)
                {"isHome": False, "goals": 1, "against": 0},  # W, Under (A)
                {"isHome": True, "goals": 4, "against": 1},   # W, Over (H)
                {"isHome": False, "goals": 2, "against": 1},  # W, Over (A)
                {"isHome": True, "goals": 1, "against": 1},   # D, Under (H)
                {"isHome": False, "goals": 0, "against": 2},  # L, Under (A)
                {"isHome": True, "goals": 3, "against": 0},   # W, Over (H)
                {"isHome": False, "goals": 2, "against": 2},  # D, Over (A)
            ]
        },
        {
            "teamName": "Liverpool",
            "matches": 19,
            "wins": 13,
            "draws": 5,
            "loses": 1,
            "scored": 42,
            "missed": 15,
            "xG": 44.8,
            "xGA": 16.5,
            "xPTS": 47.2,
            "history": [
                {"isHome": True, "goals": 2, "against": 1},   # W, Over (H)
                {"isHome": False, "goals": 3, "against": 1},  # W, Over (A)
                {"isHome": True, "goals": 1, "against": 1},   # D, Under (H)
                {"isHome": False, "goals": 2, "against": 0},  # W, Under (A)
                {"isHome": True, "goals": 3, "against": 2},   # W, Over (H)
                {"isHome": False, "goals": 1, "against": 1},  # D, Under (A)
                {"isHome": True, "goals": 2, "against": 0},   # W, Under (H)
                {"isHome": False, "goals": 3, "against": 0},  # W, Over (A)
                {"isHome": True, "goals": 2, "against": 1},   # W, Over (H)
                {"isHome": False, "goals": 1, "against": 0},  # W, Under (A)
            ]
        },
        {
            "teamName": "Arsenal",
            "matches": 20,
            "wins": 12,
            "draws": 5,
            "loses": 3,
            "scored": 40,
            "missed": 20,
            "xG": 42.3,
            "xGA": 21.7,
            "xPTS": 43.5,
            "history": [
                {"isHome": True, "goals": 2, "against": 0},   # W, Under (H)
                {"isHome": False, "goals": 1, "against": 2},  # L, Over (A)
                {"isHome": True, "goals": 3, "against": 1},   # W, Over (H)
                {"isHome": False, "goals": 0, "against": 0},  # D, Under (A)
                {"isHome": True, "goals": 1, "against": 1},   # D, Under (H)
                {"isHome": False, "goals": 2, "against": 3},  # L, Over (A)
                {"isHome": True, "goals": 2, "against": 1},   # W, Over (H)
                {"isHome": False, "goals": 1, "against": 1},  # D, Under (A)
                {"isHome": True, "goals": 3, "against": 2},   # W, Over (H)
                {"isHome": False, "goals": 2, "against": 0},  # W, Under (A)
            ]
        },
    ]
    
    for team in sample_teams:
        team['league'] = league
        team['season'] = season
    
    return sample_teams


# Example usage
if __name__ == "__main__":
    print("\n" + "="*70)
    print("UNDERSTAT SCRAPER - TEST")
    print("="*70)
    print("\nNOTE: Understat uses client-side rendering.")
    print("For best results, use: UnderstatScraper(use_selenium=True)")
    print("Or use get_sample_data() for testing the database integration.")
    print("="*70)
    
    # Test with requests (may not work)
    print("\n1. Testing with requests (likely to fail)...")
    with UnderstatScraper(use_selenium=False) as scraper:
        try:
            data = scraper.fetch_data("EPL", 2024)
            if data:
                print(f"✓ Success! Fetched {len(data)} teams")
                print(json.dumps(data[0], indent=2))
            else:
                print("✗ No data returned (expected due to client-side rendering)")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Show sample data option
    print("\n2. Using sample data for testing...")
    sample = get_sample_data("EPL", 2024)
    print(f"✓ Generated {len(sample)} sample teams")
    print(json.dumps(sample[0], indent=2))
