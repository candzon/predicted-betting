"""
Advanced Betting Analysis Tool v3.0 (Indonesian Version)
--------------------------------------------------------
Fitur:
- Bahasa Indonesia yang mudah dimengerti.
- Istilah betting lokal (Lek-lekan, Tumpul, Tajam).
- Visual warna terminal.
"""

import asyncio
import math
import sys
from typing import Dict, List, Optional
from prisma import Prisma
from prisma.models import TeamStats

# Warna untuk Terminal (Agar enak dilihat)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m' # Kuning
    FAIL = '\033[91m'    # Merah
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class BettingAnalyzer:
    """Analisis betting canggih."""
    
    def __init__(self):
        self.db = Prisma()
    
    async def connect(self):
        await self.db.connect()
    
    async def disconnect(self):
        await self.db.disconnect()
    
    async def get_team_stats(self, team_name: str, league: str, season: int) -> Optional[TeamStats]:
        return await self.db.teamstats.find_first(
            where={
                'teamName': team_name,
                'league': league,
                'season': season
            }
        )
    
    async def predict_match(self, home_team: str, away_team: str, league: str, season: int = 2025) -> Dict:
        """
        Prediksi pertandingan menggunakan Model Kekuatan Serangan/Pertahanan.
        """
        # 1. AMBIL DATA
        home = await self.get_team_stats(home_team, league, season)
        away = await self.get_team_stats(away_team, league, season)
        
        if not home or not away: return {'error': f'Tim tidak ditemukan: {home_team} atau {away_team}'}
        if home.matches == 0 or away.matches == 0: return {'error': 'Data pertandingan belum cukup (0 match)'}

        # 2. HITUNG RATA-RATA LIGA
        league_teams = await self.db.teamstats.find_many(where={'league': league, 'season': season})
        total_xg = sum(t.xG for t in league_teams)
        total_matches = sum(t.matches for t in league_teams)
        
        if total_matches == 0: return {'error': 'Data liga kosong'}
        LEAGUE_AVG_GOALS = total_xg / total_matches

        # 3. HITUNG KEKUATAN (STRENGTH)
        # > 1.0 = Kuat/Tajam, < 1.0 = Lemah/Tumpul
        home_att_str = (home.xG / home.matches) / LEAGUE_AVG_GOALS
        home_def_str = (home.xGA / home.matches) / LEAGUE_AVG_GOALS
        away_att_str = (away.xG / away.matches) / LEAGUE_AVG_GOALS
        away_def_str = (away.xGA / away.matches) / LEAGUE_AVG_GOALS

        # 4. HITUNG EKSPEKTASI GOL
        HOME_FIELD_FACTOR = 1.15 # Tuan rumah biasanya 15% lebih jago
        home_expected = home_att_str * away_def_str * LEAGUE_AVG_GOALS * HOME_FIELD_FACTOR
        away_expected = away_att_str * home_def_str * LEAGUE_AVG_GOALS

        # --- UPDATE v3.0: KOREKSI PERTANDINGAN ALOT ---
        # Jika kedua tim serangan tumpul (< 1.0), kurangi prediksi gol.
        if home_att_str < 1.0 and away_att_str < 1.0:
            CORRECTION_FACTOR = 0.85 # Diskon gol 15%
            home_expected *= CORRECTION_FACTOR
            away_expected *= CORRECTION_FACTOR
            correction_msg = "⚠️ Laga Alot! (Potensi Gol Turun 15%)"
        else:
            correction_msg = ""

        total_goals_proj = home_expected + away_expected
        
        # 5. POISSON DISTRIBUTION (Simulasi Peluang)
        def poisson_probability(k, lamb):
            return (lamb ** k * math.exp(-lamb)) / math.factorial(k)

        prob_home_win, prob_draw, prob_away_win = 0.0, 0.0, 0.0
        prob_under_2_5_sum = 0.0

        # Simulasi matriks skor 0-6
        for h in range(7):
            for a in range(7):
                prob = poisson_probability(h, home_expected) * poisson_probability(a, away_expected)
                
                # Peluang Menang
                if h > a: prob_home_win += prob
                elif h == a: prob_draw += prob
                else: prob_away_win += prob
                
                # Peluang Under 2.5
                if (h + a) < 2.5: 
                    prob_under_2_5_sum += prob

        prob_home_pct = prob_home_win * 100
        prob_draw_pct = prob_draw * 100
        prob_away_pct = prob_away_win * 100
        prob_under_pct = prob_under_2_5_sum * 100
        prob_over_pct = 100 - prob_under_pct

        # 6. LOGIKA PEMENANG (Bahasa Indonesia)
        if prob_home_pct > prob_away_pct + 10:
            winner = f"{home_team} (Tuan Rumah)"
            conf_val = prob_home_pct
        elif prob_away_pct > prob_home_pct + 10:
            winner = f"{away_team} (Tamu)"
            conf_val = prob_away_pct
        else:
            winner = "Seri / Berisiko (Skip)"
            conf_val = prob_draw_pct

        if conf_val > 60: win_conf = "TINGGI 🔥"
        elif conf_val > 45: win_conf = "SEDANG ⚖️"
        else: win_conf = "RENDAH ⚠️"

        # 7. LOGIKA OVER/UNDER
        if prob_over_pct > 55:
            over_under = "OVER 2.5 (Banjir Gol)"
            ou_val = prob_over_pct
        elif prob_under_pct > 55:
            over_under = "UNDER 2.5 (Sepi Gol)"
            ou_val = prob_under_pct
        else:
            over_under = "SKIP (Pasar Bingung 50:50)"
            ou_val = 50.0

        if ou_val > 65: ou_conf = "TINGGI 🔥"
        elif ou_val > 55: ou_conf = "SEDANG ⚖️"
        else: ou_conf = "RENDAH ⚠️"

        # 8. BTTS & HANDICAP
        btts = "YA" if home_expected > 1.10 and away_expected > 1.10 else "TIDAK"
        
        raw_diff = home_expected - away_expected
        abs_diff = abs(raw_diff)
        fav = home_team if raw_diff > 0 else away_team
        
        if abs_diff < 0.15: hdp = "0.0 (Lek-lekan)"
        elif abs_diff < 0.37: hdp = f"{fav} -0.25 (Voor Tipis)"
        elif abs_diff < 0.62: hdp = f"{fav} -0.50 (Menang Mutlak)"
        elif abs_diff < 0.87: hdp = f"{fav} -0.75"
        elif abs_diff < 1.12: hdp = f"{fav} -1.0"
        else: hdp = f"{fav} -1.25+"

        return {
            'home': home_team, 'away': away_team,
            'score': f"{home_expected:.2f} - {away_expected:.2f}",
            'total': f"{total_goals_proj:.2f}",
            'probs': {'h': prob_home_pct, 'd': prob_draw_pct, 'a': prob_away_pct},
            'winner': {'pick': winner, 'conf': win_conf},
            'ou': {'pick': over_under, 'conf': ou_conf, 'prob': ou_val},
            'btts': btts, 'hdp': hdp, 'msg': correction_msg,
            'stats': {
                'home_att': home_att_str, 'home_def': home_def_str,
                'away_att': away_att_str, 'away_def': away_def_str
            }
        }

# CLI Interface
async def main():
    analyzer = BettingAnalyzer()
    await analyzer.connect()
    
    try:
        if len(sys.argv) < 5:
            print(f"{Colors.WARNING}Cara Pakai: python betting_analyzer.py predict <home> <away> <league> [season]{Colors.ENDC}")
            return
            
        if sys.argv[1] == "predict":
            res = await analyzer.predict_match(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]) if len(sys.argv) > 5 else 2025)
            if 'error' in res:
                print(f"{Colors.FAIL}❌ Error: {res['error']}{Colors.ENDC}")
                return

            # Logika Warna
            win_color = Colors.GREEN if "TINGGI" in res['winner']['conf'] else Colors.WARNING if "SEDANG" in res['winner']['conf'] else Colors.FAIL
            ou_color = Colors.GREEN if "TINGGI" in res['ou']['conf'] else Colors.WARNING if "SEDANG" in res['ou']['conf'] else Colors.FAIL
            
            # Helper Status (Tumpul/Tajam/Bocor)
            def get_status(val, is_att=True):
                if is_att: return "🔥 Tajam" if val > 1.1 else "⚠️ Tumpul" if val < 0.9 else "Standar"
                else: return "🛡️ Kuat" if val < 0.9 else "⚠️ Bocor" if val > 1.1 else "Standar"

            print(f"""
{Colors.HEADER}╔════════════════════════════════════════════════════════════════╗
║             PREDIKSI PERTANDINGAN BOLA v3.0 (INDO)             ║
╚════════════════════════════════════════════════════════════════╝{Colors.ENDC}
🏟️  {Colors.BOLD}{res['home']} vs {res['away']}{Colors.ENDC}
   Peluang: Tuan Rumah {res['probs']['h']:.1f}% | Seri {res['probs']['d']:.1f}% | Tamu {res['probs']['a']:.1f}%

📊 PREDIKSI SKOR: {Colors.CYAN}{res['score']}{Colors.ENDC} (Total: {res['total']})
   {Colors.FAIL}{res['msg']}{Colors.ENDC}

🏆 PEMENANG: {win_color}{res['winner']['pick']} ({res['winner']['conf']}){Colors.ENDC}
⚽ O/U:      {ou_color}{res['ou']['pick']} ({res['ou']['prob']:.1f}%){Colors.ENDC}
🎯 BTTS:     {res['btts']} (Kedua Tim Gol)
📐 HANDICAP: {Colors.BLUE}{res['hdp']}{Colors.ENDC}

─────────────────────────────────────────────────────────────────
{Colors.BOLD}KEKUATAN TUAN RUMAH (1.0 = Rata-rata){Colors.ENDC}
  Serangan  : {res['stats']['home_att']:.2f} [{get_status(res['stats']['home_att'], True)}]
  Pertahanan: {res['stats']['home_def']:.2f} [{get_status(res['stats']['home_def'], False)}]

{Colors.BOLD}KEKUATAN TIM TAMU{Colors.ENDC}
  Serangan  : {res['stats']['away_att']:.2f} [{get_status(res['stats']['away_att'], True)}]
  Pertahanan: {res['stats']['away_def']:.2f} [{get_status(res['stats']['away_def'], False)}]
═════════════════════════════════════════════════════════════════
            """)

    finally:
        await analyzer.disconnect()

if __name__ == "__main__":
    asyncio.run(main())