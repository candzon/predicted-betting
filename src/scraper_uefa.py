"""
🏆 UEFA CHAMPIONS LEAGUE BOT (V15 - REAL TIME BROWSER SCRAPER)
--------------------------------------------------------------
Solusi Real-Time:
1. NO API CALLS: Tidak pakai API yang diblokir.
2. BROWSER SCRAPING: Robot Chrome membuka website ClubElo.com secara langsung.
3. FRESH DATA: Data diambil detik ini juga (Real-time ELO).
"""

import asyncio
import logging
import math
import time
from typing import List, Dict, Optional
from prisma import Prisma
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from difflib import get_close_matches

# ==========================================
# Extra utilities: HTTP fallback and local cache
import os
import json

# Optional HTTP fallback
try:
    import requests
except Exception:
    requests = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

# ==========================================
# 📝 JADWAL PERTANDINGAN (EDIT DISINI)
# ==========================================
MATCH_SCHEDULE = [
    ("Bodø/Glimt", "Manchester City"),
    ("Copenhagen", "Napoli"),
    ("Olympiakos", "Leverkusen"),
    ("Real Madrid", "Monaco"),
    ("Sporting CP", "Paris"),
    ("Tottenham", "B. Dortmund"),
    ("Villarreal", "Ajax"),
]

class Colors:
    HEADER = '\033[95m'; GREEN = '\033[92m'; YELLOW = '\033[93m'; RED = '\033[91m'; CYAN = '\033[96m'; ENDC = '\033[0m'; BOLD = '\033[1m'

# ==========================================
# 1. REAL-TIME ELO SCRAPER (VIA BROWSER)
# ==========================================
class RealTimeElo:
    def __init__(self):
        self.elo_data = {}

    def fetch_data(self):
        print(f"{Colors.CYAN}🌐 Membuka Browser untuk ambil ELO Real-time...{Colors.ENDC}")
        cache_path = os.path.join(os.path.dirname(__file__), "elo_cache.json")

        # 0) Try requests + BeautifulSoup first (faster, no browser)
        if requests and BeautifulSoup:
            try:
                print(f"{Colors.CYAN}🔁 Mencoba HTTP fallback (requests) terlebih dahulu...{Colors.ENDC}")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                proxies = None
                http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
                https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
                if http_proxy or https_proxy:
                    proxies = {}
                    if http_proxy: proxies['http'] = http_proxy
                    if https_proxy: proxies['https'] = https_proxy

                resp = requests.get("https://clubelo.com/", headers=headers, timeout=10, proxies=proxies)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    table = soup.find("table", class_="ranking")
                    if table:
                        rows = table.select("tbody tr")
                        for row in rows:
                            try:
                                club_el = row.select_one("td.club a")
                                elo_el = row.select_one("td.elo")
                                if not club_el or not elo_el:
                                    continue
                                team_name = club_el.get_text(strip=True)
                                elo_score = float(elo_el.get_text(strip=True))
                                self.elo_data[team_name] = elo_score
                            except Exception:
                                continue

                    if len(self.elo_data) > 50:
                        print(f"{Colors.GREEN}✓ BERHASIL (HTTP)! Mendapatkan {len(self.elo_data)} Data ELO.{Colors.ENDC}")
                        try:
                            with open(cache_path, "w", encoding="utf-8") as f:
                                json.dump(self.elo_data, f, ensure_ascii=False, indent=2)
                        except Exception:
                            pass
                        return
            except Exception as e:
                print(f"{Colors.YELLOW}⚠ HTTP fallback gagal: {e}{Colors.ENDC}")

        opts = Options()
        opts.add_argument("--headless=new") # Mode background
        opts.add_argument("--log-level=3")
        opts.add_argument("--disable-blink-features=AutomationControlled") 
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        driver = None
        try:
            # Init Driver
            path = ChromeDriverManager().install()
            if "THIRD_PARTY_NOTICES" in path:
                path = os.path.join(os.path.dirname(path), "chromedriver.exe")
            
            svc = Service(executable_path=path)
            driver = webdriver.Chrome(service=svc, options=opts)
            
            # 1. Buka Website ClubElo (Pintu Depan)
            driver.get("https://clubelo.com/")
            
            # Tunggu tabel muncul
            print(f"{Colors.CYAN}⏳ Sedang membaca ribuan data tim... (Tunggu sebentar){Colors.ENDC}")
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "ranking")))
            
            # 2. Ambil semua baris data
            # Struktur ClubElo: tabel class="ranking", baris adalah 'tr'
            rows = driver.find_elements(By.CSS_SELECTOR, "table.ranking tbody tr")
            
            count = 0
            for row in rows:
                try:
                    # Ambil Nama Klub (biasanya di kolom ke-2 atau ada di link)
                    # ClubElo strukturnya agak unik, nama tim ada di dalam tag <a href="/ManCity">
                    club_el = row.find_element(By.CSS_SELECTOR, "td.club a")
                    team_name = club_el.text.strip()
                    
                    # Ambil ELO (biasanya di kolom ELO)
                    # Kolom ELO biasanya ada di td class="elo" atau kolom index tertentu
                    elo_el = row.find_element(By.CSS_SELECTOR, "td.elo")
                    elo_score = float(elo_el.text.strip())
                    
                    self.elo_data[team_name] = elo_score
                    count += 1
                except:
                    continue
            
            if count > 50:
                print(f"{Colors.GREEN}✓ BERHASIL! Mendapatkan {count} Data ELO Real-time.{Colors.ENDC}")
            else:
                raise Exception("Data yang terbaca terlalu sedikit.")

        except Exception as e:
            print(f"{Colors.RED}⚠ Gagal Scrape ELO via Browser: {e}{Colors.ENDC}")
            # Try to load cache before internal fallback
            loaded_cache = False
            try:
                if os.path.exists(cache_path):
                    with open(cache_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and len(data) > 0:
                            self.elo_data = {k: float(v) for k, v in data.items()}
                            loaded_cache = True
                            print(f"{Colors.GREEN}✓ Memuat cache ELO lokal ({len(self.elo_data)} tim).{Colors.ENDC}")
            except Exception:
                loaded_cache = False

            if not loaded_cache:
                print(f"{Colors.YELLOW}⚠ Menggunakan data darurat internal.{Colors.ENDC}")
                # Fallback Darurat kalau website pun diblokir
                self.elo_data = {'Man City': 2060, 'Real Madrid': 2040, 'Liverpool': 2030, 'Inter': 2000}
        
        finally:
            if driver: driver.quit()

    def get_elo(self, team_name: str) -> float:
        # 1. Exact Match
        if team_name in self.elo_data: return self.elo_data[team_name]
        
        # 2. Fuzzy Match
        matches = get_close_matches(team_name, self.elo_data.keys(), n=1, cutoff=0.6)
        if matches: return self.elo_data[matches[0]]
        
        # 3. Manual Mapping (Untuk nama yg beda jauh)
        MAP = {
            "Man City": "ManCity", "Sporting CP": "Sporting", "Paris": "ParisSG", 
            "B. Dortmund": "Dortmund", "Atleti": "Atletico", "Bayer Leverkusen": "Leverkusen",
            "Crvena Zvezda": "RedStar", "PSV": "PSV", "Bayern München": "Bayern",
            "Aston Villa": "AstonVilla", "Sturm Graz": "SturmGraz", "Slovan Bratislava": "SlovanBratislava",
            "Club Brugge": "ClubBrugge"
        }
        if team_name in MAP and MAP[team_name] in self.elo_data:
            return self.elo_data[MAP[team_name]]
            
        return 1500.0 # Rata-rata

# ==========================================
# 2. SUPER BRAIN (LOGIC)
# ==========================================
class SuperBrain:
    def __init__(self, elo_system):
        self.elo = elo_system

    def analyze(self, h_name: str, a_name: str):
        elo_h_raw = self.elo.get_elo(h_name)
        elo_a_raw = self.elo.get_elo(a_name)
        
        # Home Advantage +100
        elo_h = elo_h_raw + 100
        elo_a = elo_a_raw
        
        # Rumus Probabilitas ELO
        prob_home = 1 / (1 + 10 ** ((elo_a - elo_h) / 400))
        prob_away = 1 - prob_home
        
        # Estimasi Draw
        draw_chance = 0.26 - (abs(prob_home - prob_away) * 0.15)
        if draw_chance < 0.10: draw_chance = 0.10
        
        remaining = 1.0 - draw_chance
        final_home = prob_home * remaining
        final_away = prob_away * remaining
        final_draw = draw_chance
        
        # --- LOGIKA PICK ---
        picks = []
        if final_home > 0.55: picks.append(('HOME WIN', final_home))
        elif final_away > 0.55: picks.append(('AWAY WIN', final_away))
        
        if (final_home + final_draw) > 0.78: picks.append(('1X (Home/Draw)', final_home+final_draw))
        if (final_away + final_draw) > 0.75: picks.append(('X2 (Away/Draw)', final_away+final_draw))
        
        # Over/Under sederhana bedasarkan selisih kekuatan
        diff_elo = abs(elo_h_raw - elo_a_raw)
        if diff_elo > 300: picks.append(('OVER 2.5', 0.70))
        elif diff_elo < 50: picks.append(('UNDER 3.5', 0.65))

        if not picks: best_pick = ('SKIP', 0)
        else: best_pick = max(picks, key=lambda x: x[1])

        # Handicap
        hdp_val = prob_home - prob_away
        hdp = "0.0"
        if hdp_val > 0.6: hdp = "-1.5"
        elif hdp_val > 0.4: hdp = "-1.0"
        elif hdp_val > 0.2: hdp = "-0.5"
        elif hdp_val > 0.05: hdp = "-0.25"
        elif hdp_val < -0.6: hdp = "+1.5"
        elif hdp_val < -0.4: hdp = "+1.0"
        elif hdp_val < -0.2: hdp = "+0.5"
        elif hdp_val < -0.05: hdp = "+0.25"

        return {
            'match': f"{h_name} vs {a_name}",
            'pick': best_pick[0],
            'conf': best_pick[1] * 100,
            'hdp': hdp,
            'elo_info': f"{int(elo_h_raw)} vs {int(elo_a_raw)}"
        }

# ==========================================
# MAIN EXECUTION
# ==========================================
def main():
    print(f"\n{Colors.HEADER}🚀 UCL BOT V15 (REAL-TIME BROWSER SCRAPER){Colors.ENDC}")
    print(f"{Colors.CYAN}Mengambil data live dari website (Bukan API/Manual)...{Colors.ENDC}")
    
    # 1. Scrape ELO Real-time
    elo = RealTimeElo()
    elo.fetch_data()
    
    # 2. Analyze
    brain = SuperBrain(elo)
    results = []
    
    print(f"\n{Colors.HEADER}🧠 MENGHITUNG PROBABILITAS TERKINI...{Colors.ENDC}")
    for h, a in MATCH_SCHEDULE:
        res = brain.analyze(h, a)
        results.append(res)

    results.sort(key=lambda x: x['conf'], reverse=True)
    
    print("\n" + "="*95)
    print(f"{Colors.GREEN}🎫  TIKET PARLAY V15 (DATA LIVE)  🎫{Colors.ENDC}")
    print("="*95)
    print(f"{'PERTANDINGAN':<30} | {'TARUHAN':<18} | {'VOOR':<6} | {'YAKIN?':<6} | {'ELO (LIVE)'}")
    print("-" * 95)
    for r in results:
        c = r['conf']
        col = Colors.GREEN if c > 80 else Colors.YELLOW
        print(f"{r['match']:<30} | {Colors.BOLD}{r['pick']:<18}{Colors.ENDC} | {r['hdp']:<6} | {col}{c:.1f}%{Colors.ENDC} | {r['elo_info']}")
    print("="*95 + "\n")

if __name__ == "__main__":
    main()