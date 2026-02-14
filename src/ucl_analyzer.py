"""
Advanced Betting Analysis Tool v3.1 (UCL Special Edition)
---------------------------------------------------------
Updates:
- Added 'League Coefficients': Normalizes stats across different countries.
- Solves the 'Domestic Bully' problem (e.g., strong stats in weak leagues).
"""

import asyncio
import math
import sys
from typing import Dict, List, Optional
from prisma import Prisma
from prisma.models import TeamStats

# --- NEW: KOEFISIEN LIGA (Berdasarkan Ranking UEFA/Power Ranking) ---
# Angka > 1.0 = Liga Elite (Stats akan diboost)
# Angka < 1.0 = Liga Lemah (Stats akan dipangkas)
LEAGUE_COEFFICIENTS = {
    'EPL': 1.15,        # Inggris (Terkeras)
    'La_Liga': 1.05,    # Spanyol
    'Serie_A': 1.00,    # Italia (Benchmark Standar)
    'Bundesliga': 1.00, # Jerman
    'Ligue_1': 0.90,    # Prancis
    'Eredivisie': 0.80, # Belanda
    'Primeira': 0.85,   # Portugal
    'Others': 0.70      # Liga lain (Austria, Swiss, dll)
}

# ANSI Colors (Tetap Sama)
class Colors:
    HEADER = '\033[95m'; BLUE = '\033[94m'; CYAN = '\033[96m'; GREEN = '\033[92m'
    WARNING = '\033[93m'; FAIL = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'

class BettingAnalyzer:
    def __init__(self):
        self.db = Prisma()
    
    async def connect(self): await self.db.connect()
    async def disconnect(self): await self.db.disconnect()
    
    async def get_team_stats(self, team_name: str) -> Optional[TeamStats]:
        # HAPUS filter 'league' di sini karena di UCL tim beda liga
        # Kita cari berdasarkan nama tim saja di musim terbaru
        return await self.db.teamstats.find_first(
            where={'teamName': team_name, 'season': 2025}
        )
    
    async def predict_ucl(self, home_team: str, away_team: str) -> Dict:
        """
        Special Prediction Logic for Champions League using Weighted Stats.
        """
        # 1. AMBIL DATA
        home = await self.get_team_stats(home_team)
        away = await self.get_team_stats(away_team)
        
        if not home or not away: return {'error': f'Team not found'}

        # 2. DETEKSI ASAL LIGA & AMBIL KOEFISIEN
        # Asumsi: Di database Anda ada kolom 'league' untuk setiap tim
        h_league = home.league if home.league in LEAGUE_COEFFICIENTS else 'Others'
        a_league = away.league if away.league in LEAGUE_COEFFICIENTS else 'Others'
        
        h_weight = LEAGUE_COEFFICIENTS[h_league]
        a_weight = LEAGUE_COEFFICIENTS[a_league]

        # 3. HITUNG RAW STATS (Rata-rata per match)
        # Di UCL, kita pakai standar rata-rata gol Eropa (~1.6 per tim) sebagai penyebut
        UCL_AVG_GOALS = 1.60 

        # 4. TERAPKAN BOBOT LIGA (CRUCIAL STEP!)
        # Attack dikali Weight (Liga kuat attack-nya lebih berharga)
        # Defense dibagi Weight (Liga kuat defense-nya lebih sulit ditembus, jadi angkanya diperkecil/dibagusin)
        
        home_att_str = ((home.xG / home.matches) / UCL_AVG_GOALS) * h_weight
        home_def_str = ((home.xGA / home.matches) / UCL_AVG_GOALS) / h_weight # Defense makin kecil makin bagus
        
        away_att_str = ((away.xG / away.matches) / UCL_AVG_GOALS) * a_weight
        away_def_str = ((away.xGA / away.matches) / UCL_AVG_GOALS) / a_weight

        # 5. HITUNG EXPECTED GOALS
        HOME_FIELD_FACTOR = 1.12 # Sedikit dikurangi untuk UCL karena faktor netral/travel
        
        home_expected = home_att_str * away_def_str * UCL_AVG_GOALS * HOME_FIELD_FACTOR
        away_expected = away_att_str * home_def_str * UCL_AVG_GOALS

        # --- BLUNT ATTACK PENALTY (Tetap Dipakai) ---
        if home_att_str < 1.0 and away_att_str < 1.0:
            home_expected *= 0.85
            away_expected *= 0.85
            msg = "⚠️ Low Quality (Weak Teams)"
        # --- NEW: MISMATCH CORRECTION ---
        # Jika tim Elite (Att > 1.3) ketemu tim lemah (Def > 1.3)
        elif home_att_str > 1.3 and away_def_str > 1.3:
            home_expected *= 1.1 # Boost gol untuk pembantaian
            msg = "🔥 Potential Mismatch/Thrashing"
        else:
            msg = ""

        total_proj = home_expected + away_expected

        # 6. POISSON (Sama seperti v3.0)
        prob_home, prob_draw, prob_away, prob_under = 0.0, 0.0, 0.0, 0.0
        
        for h in range(7):
            for a in range(7):
                p = (home_expected**h * math.exp(-home_expected) / math.factorial(h)) * \
                    (away_expected**a * math.exp(-away_expected) / math.factorial(a))
                
                if h > a: prob_home += p
                elif h == a: prob_draw += p
                else: prob_away += p
                
                if (h+a) < 2.5: prob_under += p

        # 7. LOGIKA OUTPUT (Disederhanakan untuk UCL)
        p_home_pct = prob_home * 100
        p_away_pct = prob_away * 100
        
        if p_home_pct > p_away_pct + 15: winner = f"{home_team} (Home)"
        elif p_away_pct > p_home_pct + 15: winner = f"{away_team} (Away)"
        else: winner = "Draw / Risky"

        return {
            'home': home_team, 'away': away_team,
            'h_league': h_league, 'a_league': a_league,
            'score': f"{home_expected:.2f} - {away_expected:.2f}",
            'total': total_proj,
            'probs': [p_home_pct, prob_draw*100, p_away_pct],
            'winner': winner,
            'msg': msg,
            'u_prob': prob_under * 100
        }

# CLI Interface
async def main():
    analyzer = BettingAnalyzer()
    await analyzer.connect()
    
    if len(sys.argv) < 3:
        print("Usage: python ucl_analyzer.py predict <home> <away>")
        return

    res = await analyzer.predict_ucl(sys.argv[2], sys.argv[3])
    if 'error' in res: print(res['error']); return

    print(f"""
{Colors.HEADER}╔════ UCL NIGHT PREDICTION v3.1 ════╗{Colors.ENDC}
 ⚔️  {Colors.BOLD}{res['home']}{Colors.ENDC} ({res['h_league']}) vs {Colors.BOLD}{res['away']}{Colors.ENDC} ({res['a_league']})
    Win Probs: {res['probs'][0]:.1f}% | {res['probs'][1]:.1f}% | {res['probs'][2]:.1f}%

 📊 Score: {Colors.CYAN}{res['score']}{Colors.ENDC} (Total: {res['total']:.2f})
    {Colors.WARNING}{res['msg']}{Colors.ENDC}

 🏆 Winner: {Colors.GREEN}{res['winner']}{Colors.ENDC}
 ⚽ O/U:    {'UNDER 2.5' if res['u_prob'] > 55 else 'OVER 2.5'} ({res['u_prob']:.1f}% Under)
""")
    
    await analyzer.disconnect()

if __name__ == "__main__":
    asyncio.run(main())