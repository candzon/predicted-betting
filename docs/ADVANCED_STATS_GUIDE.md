# Understat Advanced Statistics - Dokumentasi Lengkap

## Overview

Script ini telah diupdate untuk mengekstrak statistik mendalam dari Understat.com meliputi:

1. **Form 10 Pertandingan Terakhir** - W/D/L dan total poin
2. **Home vs Away Split** - Statistik terpisah untuk kandang dan tandang  
3. **Tren Over/Under 2.5** - Persentase pertandingan Over 2.5 goals

---

## 🚀 Quick Start

### 1. Update Database Schema

```bash
# Generate Prisma client dengan schema baru
prisma generate

# Push schema ke database
prisma db push
```

### 2. Test Fungsi Baru

```bash
# Jalankan test script
python test_advanced_stats.py
```

### 3. Scrape Data

```bash
# Jalankan scraper (dengan Selenium untuk data real)
python main.py
```

---

## 📊 Field Baru di Database

### Form 10 Pertandingan Terakhir

| Field | Type | Deskripsi | Contoh |
|-------|------|-----------|---------|
| `last10_form` | String | String hasil (W/D/L) | `"WWDLWWDWWL"` |
| `last10_wins` | Int | Jumlah menang | `6` |
| `last10_draws` | Int | Jumlah seri | `3` |
| `last10_loses` | Int | Jumlah kalah | `1` |
| `last10_points` | Int | Total poin (W=3, D=1, L=0) | `21` |

### Tren Over/Under 2.5 Goals

| Field | Type | Deskripsi | Contoh |
|-------|------|-----------|---------|
| `last10_over` | Int | Jumlah pertandingan Over 2.5 | `6` |
| `last10_under` | Int | Jumlah pertandingan Under 2.5 | `4` |
| `last10_over_pct` | Float | Persentase Over 2.5 | `60.0` |

### Home Statistics (Kandang)

| Field | Type | Deskripsi |
|-------|------|-----------|
| `home_wins` | Int | Menang di kandang |
| `home_draws` | Int | Seri di kandang |
| `home_loses` | Int | Kalah di kandang |
| `home_over` | Int | Over 2.5 di kandang |

### Away Statistics (Tandang)

| Field | Type | Deskripsi |
|-------|------|-----------|
| `away_wins` | Int | Menang di tandang |
| `away_draws` | Int | Seri di tandang |
| `away_loses` | Int | Kalah di tandang |
| `away_over` | Int | Over 2.5 di tandang |

---

## 💻 Kode Python - Fungsi Utama

### 1. `_compute_recent_stats(team_raw: Dict) -> Dict`

Fungsi ini mengekstrak dan menghitung semua statistik lanjutan dari data history tim.

**Input:**
```python
team_raw = {
    "teamName": "Manchester City",
    "history": [
        {"isHome": True, "goals": 3, "against": 1},   # W, Over
        {"isHome": False, "goals": 2, "against": 0},  # W, Under
        # ... 8 pertandingan lagi
    ]
}
```

**Output:**
```python
{
    'last10_form': 'WWDLWWDWWL',
    'last10_wins': 6,
    'last10_draws': 3,
    'last10_loses': 1,
    'last10_points': 21,
    'last10_over': 6,
    'last10_under': 4,
    'last10_over_pct': 60.0,
    'home_wins': 3,
    'home_draws': 2,
    'home_loses': 0,
    'home_over': 4,
    'away_wins': 3,
    'away_draws': 1,
    'away_loses': 1,
    'away_over': 2,
}
```

**Logika Perhitungan:**

```python
# 1. Ambil 10 pertandingan terakhir
recent_matches = matches_list[-10:]

# 2. Loop setiap pertandingan
for match in recent_matches:
    # Tentukan home/away
    is_home = match['isHome']
    
    # Ekstrak gol
    goals_for = match['goals']
    goals_against = match['against']
    
    # Tentukan hasil (W/D/L) dan poin
    if goals_for > goals_against:
        result = 'W'
        points = 3
    elif goals_for == goals_against:
        result = 'D'
        points = 1
    else:
        result = 'L'
        points = 0
    
    # Hitung home/away split
    if is_home:
        home_wins += 1 if result == 'W' else 0
    else:
        away_wins += 1 if result == 'W' else 0
    
    # Hitung Over/Under 2.5
    if (goals_for + goals_against) >= 3:
        last10_over += 1
        home_over += 1 if is_home else away_over += 1

# 3. Hitung persentase
last10_over_pct = (last10_over / 10) * 100
```

---

## 📋 Schema Prisma - Update Lengkap

```prisma
model TeamStats {
  id       Int    @id @default(autoincrement())
  league   String
  season   Int
  teamName String
  
  // Statistik Dasar
  matches Int
  wins    Int
  draws   Int
  loses   Int
  scored  Int
  missed  Int
  xG      Float
  xGA     Float
  xPTS    Float
  
  // ⭐ BARU: Form 10 Pertandingan Terakhir
  last10_form   String? @default("")
  last10_wins   Int?    @default(0)
  last10_draws  Int?    @default(0)
  last10_loses  Int?    @default(0)
  last10_points Int?    @default(0)
  
  // ⭐ BARU: Tren Over/Under 2.5
  last10_over     Int?   @default(0)
  last10_under    Int?   @default(0)
  last10_over_pct Float? @default(0)
  
  // ⭐ BARU: Home Statistics
  home_wins  Int? @default(0)
  home_draws Int? @default(0)
  home_loses Int? @default(0)
  home_over  Int? @default(0)
  
  // ⭐ BARU: Away Statistics
  away_wins  Int? @default(0)
  away_draws Int? @default(0)
  away_loses Int? @default(0)
  away_over  Int? @default(0)
  
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  
  @@unique([teamName, league, season], name: "unique_team_season")
  @@index([league, season])
}
```

---

## 🎯 Use Cases - Betting Insights

### 1. Analisis Form Tim

```python
# Cari tim dengan form terbaik (5 pertandingan terakhir)
teams = await db.teamstats.find_many(
    where={'season': 2025, 'league': 'EPL'}
)

for team in teams:
    recent_form = team.last10_form[-5:]  # 5 terakhir
    wins = recent_form.count('W')
    
    if wins >= 4:
        print(f"{team.teamName}: HOT FORM ({wins}/5 wins)")
```

### 2. Analisis Over/Under Trend

```python
# Cari tim dengan tren Over 2.5 tinggi
high_over_teams = await db.teamstats.find_many(
    where={
        'season': 2025,
        'league': 'EPL',
        'last10_over_pct': {'gte': 70}  # >= 70%
    },
    order={'last10_over_pct': 'desc'}
)

for team in high_over_teams:
    print(f"{team.teamName}: {team.last10_over_pct}% Over 2.5")
```

### 3. Analisis Home/Away Split

```python
# Cari tim kuat di kandang tapi lemah di tandang
teams = await db.teamstats.find_many(
    where={'season': 2025, 'league': 'EPL'}
)

for team in teams:
    home_total = team.home_wins + team.home_draws + team.home_loses
    away_total = team.away_wins + team.away_draws + team.away_loses
    
    if home_total > 0 and away_total > 0:
        home_win_pct = (team.home_wins / home_total) * 100
        away_win_pct = (team.away_wins / away_total) * 100
        
        if home_win_pct >= 70 and away_win_pct <= 30:
            print(f"{team.teamName}: Strong Home ({home_win_pct:.1f}%), Weak Away ({away_win_pct:.1f}%)")
```

### 4. Prediksi Match

```python
async def predict_match(home_team: str, away_team: str, league: str, season: int):
    """Prediksi pertandingan berdasarkan statistik"""
    
    # Ambil data kedua tim
    home = await db.teamstats.find_first(
        where={'teamName': home_team, 'league': league, 'season': season}
    )
    away = await db.teamstats.find_first(
        where={'teamName': away_team, 'league': league, 'season': season}
    )
    
    # Analisis form
    home_form = home.last10_form[-5:].count('W')
    away_form = away.last10_form[-5:].count('W')
    
    # Analisis home advantage
    home_total = home.home_wins + home.home_draws + home.home_loses
    home_win_rate = (home.home_wins / home_total) if home_total > 0 else 0
    
    # Analisis away performance
    away_total = away.away_wins + away.away_draws + away.away_loses
    away_win_rate = (away.away_wins / away_total) if away_total > 0 else 0
    
    # Analisis Over/Under
    combined_over_pct = (home.last10_over_pct + away.last10_over_pct) / 2
    
    print(f"\n🏆 {home_team} vs {away_team}")
    print(f"   Home Form (last 5): {home_form}/5 wins")
    print(f"   Away Form (last 5): {away_form}/5 wins")
    print(f"   Home Win Rate at Home: {home_win_rate*100:.1f}%")
    print(f"   Away Win Rate Away: {away_win_rate*100:.1f}%")
    print(f"   Combined Over 2.5 Trend: {combined_over_pct:.1f}%")
    
    # Rekomendasi
    if home_win_rate > 0.7 and away_win_rate < 0.3:
        print(f"   💡 Tip: Home Win - Strong home advantage")
    
    if combined_over_pct > 70:
        print(f"   💡 Tip: Over 2.5 Goals - Both teams tend to high scoring")
    elif combined_over_pct < 30:
        print(f"   💡 Tip: Under 2.5 Goals - Both teams tend to low scoring")
```

---

## 🔧 Troubleshooting

### Problem: Field baru tidak muncul di database

**Solusi:**
```bash
# Hapus database lama dan recreate
rm betting_analysis.db

# Generate client baru
prisma generate

# Push schema
prisma db push
```

### Problem: Sample data tidak punya history

**Solusi:** Sample data di `get_sample_data()` sudah include history. Jika masih kosong, periksa file `understat_scraper.py` baris 587-653.

### Problem: Selenium error saat scraping

**Solusi:**
```bash
# Install Selenium
pip install selenium

# Download ChromeDriver yang cocok dengan versi Chrome Anda
# https://chromedriver.chromium.org/downloads
```

---

## 📈 Next Steps

1. **Tambah More Stats:**
   - Recent form terpisah (last 5 home, last 5 away)
   - Head-to-head history
   - Injury/suspension impact

2. **Machine Learning:**
   - Train model menggunakan statistik ini
   - Predict match outcomes
   - Calculate betting value

3. **Visualisasi:**
   - Chart form trends
   - Home/Away performance comparison
   - Over/Under heatmaps

---

## 📞 Support

Jika ada pertanyaan atau issues, check:
1. `test_advanced_stats.py` - untuk melihat contoh penggunaan
2. `understat_scraper.py` - untuk implementasi detail
3. `schema.prisma` - untuk struktur database

Happy Betting Analysis! 🎯⚽
