import asyncio
import math
import sys
from typing import Dict, List, Optional
# Pastikan library prisma sudah terinstall: pip install prisma
from prisma import Prisma 
from prisma.models import TeamStats

# ==========================================
# 1. VISUALISASI TERMINAL (COLORS)
# ==========================================
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m' # Kuning
    FAIL = '\033[91m'    # Merah
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ==========================================
# 2. ENGINE ANALISIS
# ==========================================
class BettingAnalyzer:
    """
    Advanced Betting Analysis Tool v4.5
    Features: Prisma DB, Last 10 Form, Home/Away Splits, Defense Damping Logic.
    """
    
    def __init__(self):
        self.db = Prisma()
    
    async def connect(self):
        await self.db.connect()
    
    async def disconnect(self):
        await self.db.disconnect()
    
    async def get_team_stats(self, team_name: str, league: str, season: int) -> Optional[TeamStats]:
        # Try exact match first
        res = await self.db.teamstats.find_first(where={
            'teamName': team_name,
            'league': league,
            'season': season
        })
        if res:
            return res

        # Fallback: case-insensitive equals
        try:
            res = await self.db.teamstats.find_first(where={
                'teamName': {'equals': team_name, 'mode': 'insensitive'},
                'league': league,
                'season': season
            })
            if res:
                return res
        except Exception:
            # Some prisma versions may not support mode on equals; ignore and continue
            pass

        # Last resort: try contains (insensitive) for partial matches (e.g., "Ac Milan" vs "AC Milan")
        try:
            res = await self.db.teamstats.find_first(where={
                'teamName': {'contains': team_name, 'mode': 'insensitive'},
                'league': league,
                'season': season
            })
            if res:
                return res
        except Exception:
            pass

        # Final fallback: fetch all teams for that league/season and match in Python (case-insensitive, normalized)
        try:
            teams = await self.db.teamstats.find_many(where={'league': league, 'season': season})
            def normalize(s: str) -> str:
                return ''.join(ch for ch in (s or '').lower() if ch.isalnum())

            target_norm = normalize(team_name)
            for t in teams:
                if normalize(t.teamName) == target_norm:
                    return t
            # try partial match
            for t in teams:
                if target_norm in normalize(t.teamName) or normalize(t.teamName) in target_norm:
                    return t
        except Exception:
            pass

        return None
    
    def calculate_poisson(self, k, lamb):
        """Rumus Poisson Distribution untuk simulasi skor."""
        return (lamb ** k * math.exp(-lamb)) / math.factorial(k)

    async def predict_match(self, home_team: str, away_team: str, league: str, season: int = 2025) -> Dict:
        """
        Core Logic Prediksi v4.5
        """
        # --- 1. AMBIL DATA DARI DATABASE ---
        home = await self.get_team_stats(home_team, league, season)
        away = await self.get_team_stats(away_team, league, season)
        
        if not home or not away: 
            return {'error': f'Data tim tidak ditemukan: {home_team} atau {away_team}'}
        if home.matches == 0 or away.matches == 0: 
            return {'error': 'Data pertandingan belum cukup (0 match)'}

        # --- 2. HITUNG RATA-RATA LIGA ---
        # Mengambil rata-rata real-time dari seluruh tim di liga tersebut
        league_teams = await self.db.teamstats.find_many(where={'league': league, 'season': season})
        total_xg = sum(t.xG for t in league_teams)
        total_matches = sum(t.matches for t in league_teams)
        
        LEAGUE_AVG_GOALS = 1.45 # Default fallback
        if total_matches > 0:
            LEAGUE_AVG_GOALS = total_xg / total_matches

        # --- 3. HITUNG KEKUATAN BASIC (Attack/Defense Strength) ---
        # Rumus: (Rata2 Tim / Rata2 Liga). >1.0 = Di atas rata-rata.
        home_att_str = (home.xG / home.matches) / LEAGUE_AVG_GOALS
        home_def_str = (home.xGA / home.matches) / LEAGUE_AVG_GOALS
        away_att_str = (away.xG / away.matches) / LEAGUE_AVG_GOALS
        away_def_str = (away.xGA / away.matches) / LEAGUE_AVG_GOALS

        # --- 4. ANALISIS MOMENTUM (Last 10 Form) ---
        home_form = home.last10_form or ""
        away_form = away.last10_form or ""
        
        def calc_form_score(form_str):
            if not form_str: return 1.0
            # Bobot: Win=3, Draw=1, Loss=0
            points = sum(3 if c == 'W' else 1 if c == 'D' else 0 for c in form_str[-10:])
            # Scaling: Hasil 0.7 (Buruk) s/d 1.3 (Bagus)
            return max(0.7, min(1.3, points / 20)) 
        
        home_form_mult = calc_form_score(home_form)
        away_form_mult = calc_form_score(away_form)

        # --- 5. ANALISIS HOME/AWAY SPLIT ---
        # Apakah tim jago kandang atau jago tandang?
        home_total_home = (home.home_wins or 0) + (home.home_draws or 0) + (home.home_loses or 0)
        away_total_away = (away.away_wins or 0) + (away.away_draws or 0) + (away.away_loses or 0)
        
        h_winrate = (home.home_wins or 0) / home_total_home if home_total_home > 0 else 0.4
        a_winrate = (away.away_wins or 0) / away_total_away if away_total_away > 0 else 0.4
        
        # Adjustment factors
        HOME_FIELD_ADVANTAGE = 1.15 + (h_winrate - 0.4) * 0.3 
        AWAY_FATIGUE = 1.0 - (0.4 - a_winrate) * 0.2 

        # --- 6. HITUNG EXPECTED GOALS (xG) AWAL ---
        home_expected = home_att_str * away_def_str * LEAGUE_AVG_GOALS * HOME_FIELD_ADVANTAGE * home_form_mult
        away_expected = away_att_str * home_def_str * LEAGUE_AVG_GOALS * AWAY_FATIGUE * away_form_mult

        # =========================================================
        # 🔥 FITUR BARU v4.5: LOGIKA DEFENSE DAMPING & TREND 🔥
        # =========================================================
        
        correction_reasons = []

        # A. Logic Defense Damping (Unstoppable Force vs Immovable Object)
        # Jika kedua tim punya Defense < 1.0 (Kuat), skor cenderung Under.
        if home_def_str < 1.0 and away_def_str < 1.0:
            damping_factor = 0.85 # Kurangi ekspektasi gol 15%
            home_expected *= damping_factor
            away_expected *= damping_factor
            correction_reasons.append("🛡️ Duel Defense Kuat (-15%)")

        # B. Logic Historical Trend Over/Under
        home_over_pct = home.last10_over_pct or 50.0
        away_over_pct = away.last10_over_pct or 50.0
        avg_over_pct = (home_over_pct + away_over_pct) / 2
        
        if avg_over_pct > 70:
            home_expected *= 1.1
            away_expected *= 1.1
            correction_reasons.append("🔥 Trend Over Tinggi (+10%)")
        elif avg_over_pct < 30:
            home_expected *= 0.9
            away_expected *= 0.9
            correction_reasons.append("💤 Trend Under Tinggi (-10%)")

        # Final Total Project
        total_goals_proj = home_expected + away_expected
        correction_msg = " | ".join(correction_reasons) if correction_reasons else "Data Normal"

        # --- 7. SIMULASI POISSON (Probabilitas Menang) ---
        prob_home_win, prob_draw, prob_away_win = 0.0, 0.0, 0.0
        prob_under_2_5_sum = 0.0

        for h in range(7): # Loop skor 0-6
            for a in range(7):
                prob = self.calculate_poisson(h, home_expected) * self.calculate_poisson(a, away_expected)
                
                if h > a: prob_home_win += prob
                elif h == a: prob_draw += prob
                else: prob_away_win += prob
                
                if (h + a) < 2.5: 
                    prob_under_2_5_sum += prob

        # Konversi ke Persen
        p_home = prob_home_win * 100
        p_draw = prob_draw * 100
        p_away = prob_away_win * 100
        p_under = prob_under_2_5_sum * 100
        p_over = 100 - p_under

        # --- 8. PENENTUAN PEMENANG & HANDICAP ---
        # Adjust sedikit probabilitas berdasarkan Home/Away Winrate real
        adj_home = p_home + (h_winrate * 5)
        adj_away = p_away + (a_winrate * 5)

        if adj_home > adj_away + 12:
            winner_pick = f"{home_team}"
            winner_conf = "TINGGI 🔥" if adj_home > 60 else "SEDANG ⚖️"
        elif adj_away > adj_home + 12:
            winner_pick = f"{away_team}"
            winner_conf = "TINGGI 🔥" if adj_away > 60 else "SEDANG ⚖️"
        else:
            winner_pick = "Seri / Berisiko (Skip)"
            winner_conf = "RENDAH ⚠️"

        # Logic Handicap
        diff = home_expected - away_expected
        if abs(diff) < 0.2: hdp = "0.0 (Lek-lekan)"
        elif diff > 0.2: hdp = f"{home_team} -0.25" if diff < 0.5 else f"{home_team} -0.5"
        else: hdp = f"{away_team} -0.25" if diff > -0.5 else f"{away_team} -0.5"

        # --- 9. PENENTUAN OVER/UNDER ---
        # Weighted: 60% Statistik Real (Trend), 40% Matematika (Poisson)
        final_over_val = (avg_over_pct * 0.6) + (p_over * 0.4)
        
        if final_over_val > 55:
            ou_pick = f"OVER 2.5"
            ou_conf_val = final_over_val
        else:
            ou_pick = f"UNDER 2.5"
            ou_conf_val = 100 - final_over_val

        ou_conf_str = "TINGGI 🔥" if ou_conf_val > 65 else "SEDANG ⚖️"

        # --- 10. PACKING RESULT ---
        return {
            'home': home_team, 'away': away_team,
            'score': f"{home_expected:.2f} - {away_expected:.2f}",
            'total': f"{total_goals_proj:.2f}",
            'probs': {'h': p_home, 'd': p_draw, 'a': p_away},
            'winner': {'pick': winner_pick, 'conf': winner_conf},
            'ou': {'pick': ou_pick, 'conf': ou_conf_str, 'val': ou_conf_val},
            'btts': "YA" if home_expected > 1.05 and away_expected > 1.05 else "TIDAK",
            'hdp': hdp, 
            'msg': correction_msg,
            'stats': {
                'home_att': home_att_str, 'home_def': home_def_str,
                'away_att': away_att_str, 'away_def': away_def_str
            },
            'form': {
                'home': home_form[-10:] if home_form else "-",
                'away': away_form[-10:] if away_form else "-",
                'home_pts': home.last10_points or 0,
                'away_pts': away.last10_points or 0
            },
            'splits': {
                'h_rec': f"{home.home_wins}W-{home.home_draws}D-{home.home_loses}L",
                'a_rec': f"{away.away_wins}W-{away.away_draws}D-{away.away_loses}L",
                'h_wr': h_winrate * 100,
                'a_wr': a_winrate * 100
            }
        }

# ==========================================
# 3. CLI HANDLER
# ==========================================
async def main():
    analyzer = BettingAnalyzer()
    await analyzer.connect()
    
    try:
        if len(sys.argv) < 5:
            print(f"{Colors.WARNING}Usage: python betting_analyzer_v4.py predict <Home> <Away> <League> [Season]{Colors.ENDC}")
            print(f"Example: python betting_analyzer_v4.py predict \"Man Utd\" \"Man City\" EPL 2025")
            return
            
        if sys.argv[1] == "predict":
            home_name = sys.argv[2]
            away_name = sys.argv[3]
            league = sys.argv[4]
            season = int(sys.argv[5]) if len(sys.argv) > 5 else 2025
            
            res = await analyzer.predict_match(home_name, away_name, league, season)
            
            if 'error' in res:
                print(f"{Colors.FAIL}❌ Error: {res['error']}{Colors.ENDC}")
                return

            # Helper Status Warna
            def stat_status(val, is_att):
                if is_att: 
                    return f"{Colors.GREEN}Tajam 🔥{Colors.ENDC}" if val > 1.1 else f"{Colors.FAIL}Tumpul ⚠️{Colors.ENDC}" if val < 0.9 else "Normal"
                else: 
                    return f"{Colors.GREEN}Kuat 🛡️{Colors.ENDC}" if val < 0.9 else f"{Colors.FAIL}Bocor ⚠️{Colors.ENDC}" if val > 1.1 else "Normal"

            # RENDER OUTPUT
            print(f"""
{Colors.HEADER}╔════════════════════════════════════════════════════════════════╗
║              PREDIKSI PERTANDINGAN BOLA v4.5 (INDO)            ║
║              🆕 WITH DEFENSE DAMPING & SPLIT STATS             ║
╚════════════════════════════════════════════════════════════════╝{Colors.ENDC}
🏟️   {Colors.BOLD}{res['home']} vs {res['away']}{Colors.ENDC}
    Peluang: Tuan Rumah {res['probs']['h']:.1f}% | Seri {res['probs']['d']:.1f}% | Tamu {res['probs']['a']:.1f}%

📊 PREDIKSI SKOR: {Colors.CYAN}{res['score']}{Colors.ENDC} (Total: {res['total']})
    {Colors.WARNING}Info: {res['msg']}{Colors.ENDC}

🏆 PEMENANG: {Colors.BOLD}{res['winner']['pick']}{Colors.ENDC} ({res['winner']['conf']})
⚽ O/U:      {Colors.BOLD}{res['ou']['pick']}{Colors.ENDC} ({res['ou']['val']:.1f}%)
🎯 BTTS:     {res['btts']} (Kedua Tim Gol)
📐 HANDICAP: {Colors.BLUE}{res['hdp']}{Colors.ENDC}

─────────────────────────────────────────────────────────────────
{Colors.BOLD}KEKUATAN TUAN RUMAH (1.0 = Rata-rata){Colors.ENDC}
  Serangan  : {res['stats']['home_att']:.2f} [{stat_status(res['stats']['home_att'], True)}]
  Pertahanan: {res['stats']['home_def']:.2f} [{stat_status(res['stats']['home_def'], False)}]

{Colors.BOLD}KEKUATAN TIM TAMU{Colors.ENDC}
  Serangan  : {res['stats']['away_att']:.2f} [{stat_status(res['stats']['away_att'], True)}]
  Pertahanan: {res['stats']['away_def']:.2f} [{stat_status(res['stats']['away_def'], False)}]

{Colors.BOLD}🔥 FORM 10 PERTANDINGAN TERAKHIR{Colors.ENDC}
  Tuan Rumah: {res['form']['home']} ({res['form']['home_pts']} poin)
  Tamu      : {res['form']['away']} ({res['form']['away_pts']} poin)

{Colors.BOLD}🏠 PERFORMA KANDANG/TANDANG{Colors.ENDC}
  {res['home']} (Home): {res['splits']['h_rec']} (WR: {res['splits']['h_wr']:.0f}%)
  {res['away']} (Away): {res['splits']['a_rec']} (WR: {res['splits']['a_wr']:.0f}%)
═════════════════════════════════════════════════════════════════
""")

    except Exception as e:
        print(f"{Colors.FAIL}Critical Error: {str(e)}{Colors.ENDC}")
    finally:
        await analyzer.disconnect()

if __name__ == "__main__":
    asyncio.run(main())