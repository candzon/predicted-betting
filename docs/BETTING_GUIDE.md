# 🎯 Panduan Betting Analysis Tool

## 📚 Konsep Dasar

### Apa itu xG, xGA, dan xPTS?

- **xG (Expected Goals)**: Berapa gol yang "seharusnya" dicetak tim berdasarkan kualitas peluang
- **xGA (Expected Goals Against)**: Berapa gol yang "seharusnya" kebobolan berdasarkan peluang lawan
- **xPTS (Expected Points)**: Berapa poin yang "seharusnya" didapat tim berdasarkan performa

### Mengapa Penting untuk Betting?

**Gap antara Expected vs Actual = Peluang Value Bet!**

- Tim dengan **xPTS >> Actual Points** → Underperforming → **Kemungkinan bounce back**
- Tim dengan **Actual Points >> xPTS** → Overperforming → **Kemungkinan decline**

---

## 🔧 Tools yang Tersedia

### 1. **Match Prediction** - Prediksi Pertandingan

Memprediksi skor, winner, over/under, BTTS berdasarkan data xG.

```bash
python betting_analyzer.py predict <home_team> <away_team> <league> [season]
```

**Contoh:**
```bash
python betting_analyzer.py predict Liverpool Arsenal EPL 2025
```

**Output:**
- Expected Score (skor prediksi)
- Winner (pemenang paling mungkin)
- Over/Under 2.5 goals
- BTTS (Both Teams To Score)
- Asian Handicap suggestion

**Cara Membaca:**
- **Expected Score 1.29 - 1.63**: Liverpool diprediksi cetak 1.29 gol, Arsenal 1.63 gol
- **OVER 2.5 (Medium)**: Total 2.92 gol, kemungkinan over moderate
- **BTTS YES (High)**: Kedua tim kemungkinan besar cetak gol
- **Asian Handicap 0.0**: Pertandingan seimbang, tidak ada handicap

---

### 2. **Value Bets** - Cari Tim yang Akan Bounce Back/Decline

Mencari tim dengan gap besar antara xPTS dan actual points.

```bash
python betting_analyzer.py value-bets [season] [min_gap]
```

**Contoh:**
```bash
python betting_analyzer.py value-bets 2025 5.0
```

**Output:**
- **Underperforming Teams**: xPTS lebih tinggi dari actual points
  - 💡 **Strategi**: BET ON tim ini untuk WIN/DRAW (mereka akan improve)
  
- **Overperforming Teams**: Actual points lebih tinggi dari xPTS
  - 💡 **Strategi**: BET AGAINST tim ini (mereka akan decline)

**Contoh Nyata:**
```
Wolverhampton Wanderers: Actual 7 pts, xPTS 20.49 (+13.49)
└─ Mereka seharusnya dapat 20 poin tapi baru 7
└─ Kemungkinan besar akan bounce back di pertandingan berikutnya
└─ ACTION: Bet Wolves untuk WIN di match berikutnya

Aston Villa: Actual 43 pts, xPTS 26.02 (-16.98)
└─ Mereka dapat 43 poin tapi seharusnya cuma 26
└─ Kemungkinan besar akan turun performa
└─ ACTION: Bet AGAINST Aston Villa
```

---

### 3. **High Scoring Matches** - Over 2.5 Goals

Mencari tim dengan kombinasi high xG + high xGA = banyak gol.

```bash
python betting_analyzer.py high-scoring <league> [season] [min_total]
```

**Contoh:**
```bash
python betting_analyzer.py high-scoring EPL 2025 3.0
```

**Strategi:**
- Tim dengan **xG + xGA > 3.0** cenderung terlibat pertandingan banyak gol
- Bet **OVER 2.5 goals** ketika tim ini main

**Contoh:**
```
Chelsea: xG 1.89, xGA 1.48, Total 3.37
└─ Chelsea rata-rata terlibat 3.37 gol per pertandingan
└─ ACTION: Bet OVER 2.5 goals di match Chelsea
```

---

### 4. **Low Scoring Matches** - Under 2.5 Goals

Mencari tim dengan xG rendah DAN xGA rendah = sedikit gol.

```bash
python betting_analyzer.py low-scoring <league> [season] [max_total]
```

**Contoh:**
```bash
python betting_analyzer.py low-scoring RFPL 2025 2.0
```

**Strategi:**
- Tim dengan **xG + xGA < 2.0** cenderung terlibat pertandingan sedikit gol
- Bet **UNDER 2.5 goals** ketika tim ini main

---

### 5. **BTTS Analysis** - Both Teams To Score

Mencari tim yang sering cetak gol DAN sering kebobolan.

```bash
python betting_analyzer.py btts <league> [season]
```

**Contoh:**
```bash
python betting_analyzer.py btts La_liga 2025
```

**Strategi:**
- Tim dengan **xG >= 1.0 DAN xGA >= 1.0** = BTTS YES candidate
- Barcelona: xG 2.66, xGA 1.49 → Skor tinggi, pertahanan lemah → **BTTS YES**

---

### 6. **Compare Teams** - Perbandingan Detail

Membandingkan statistik 2 tim secara detail.

```bash
python betting_analyzer.py compare <team1> <team2> <league> [season]
```

**Contoh:**
```bash
python betting_analyzer.py compare "Manchester City" Arsenal EPL 2025
```

**Gunakan untuk:**
- Analisis head-to-head sebelum big match
- Bandingkan attacking vs defending strength
- Lihat form recent (W-D-L)

---

## 💡 Strategi Betting Profesional

### 1. **Regression to Mean Strategy**

**Prinsip**: Tim yang underperform/overperform akan kembali ke level expected mereka.

**Cara:**
1. Cari value bets dengan gap >= 8 points
2. Bet ON underperforming teams (akan bounce back)
3. Bet AGAINST overperforming teams (akan decline)

**Contoh:**
```bash
python betting_analyzer.py value-bets 2025 8.0
```

---

### 2. **Over/Under Goals Strategy**

**Cara:**
1. Cari high-scoring teams untuk OVER bets
2. Cari low-scoring teams untuk UNDER bets
3. Gabungkan keduanya untuk confidence tinggi

**Contoh:**
```bash
# Chelsea (high xG+xGA) vs Defensive Team
python betting_analyzer.py predict Chelsea "Nottingham Forest" EPL 2025
# Jika Chelsea expected > 2.0 dan Forest < 1.0 → Bet OVER 2.5
```

---

### 3. **BTTS Strategy**

**Cara:**
1. Cari tim dengan xG >= 1.0 DAN xGA >= 1.0
2. Ketika 2 tim BTTS candidate bertemu → **HIGH confidence BTTS YES**

**Contoh:**
```bash
python betting_analyzer.py btts EPL 2025
# Jika Chelsea vs Manchester United (keduanya BTTS candidate)
# → Bet BTTS YES dengan high confidence
```

---

### 4. **Asian Handicap Strategy**

**Cara:**
1. Bandingkan xG per match kedua tim
2. Gunakan goal difference untuk handicap line

**Contoh:**
```bash
python betting_analyzer.py predict "Bayern Munich" "Mainz 05" Bundesliga 2025
# Bayern xG: 3.12, Mainz xG: 1.15
# Difference: ~2.0 goals
# → Asian Handicap Bayern -1.5 atau -2.0
```

---

### 5. **Form Analysis + xG Strategy**

**Cara:**
1. Lihat form tim (W-D-L)
2. Bandingkan dengan xG/xPTS
3. Jika form buruk tapi xG bagus → **Value bet**

**Contoh:**
```bash
python betting_analyzer.py compare Wolves Burnley EPL 2025
# Wolves: Form buruk (1W-4D-16L) tapi xPTS 20.49
# → Wolves kemungkinan bounce back soon
```

---

## 📊 Confidence Levels

### HIGH Confidence
- Gap xPTS vs Actual > 10 points
- xG difference > 1.5 goals
- BTTS score > 1.5

### MEDIUM Confidence
- Gap 5-10 points
- xG difference 0.5-1.5 goals
- BTTS score 1.0-1.5

### LOW Confidence
- Gap < 5 points
- xG difference < 0.5 goals
- Pertandingan seimbang

---

## ⚠️ Warning & Tips

### ❌ Jangan:
1. Bet hanya berdasarkan 1 metric saja
2. Ignore form recent (5 games terakhir)
3. Bet semua tim underperforming (pilih yang terbaik)
4. Forget tentang injury, suspension, motivation

### ✅ Lakukan:
1. Kombinasikan multiple metrics (xG + xGA + xPTS + form)
2. Focus pada HIGH confidence bets
3. Bankroll management (max 5% per bet)
4. Track your bets dan evaluate

---

## 🎓 Contoh Kasus Nyata

### Kasus 1: Value Bet - Wolverhampton

```bash
python betting_analyzer.py value-bets 2025 5.0
```

**Data:**
- Actual Points: 7
- xPTS: 20.49
- Gap: +13.49

**Analysis:**
- Wolves seharusnya dapat 20 poin, tapi baru 7
- Ini gap SANGAT besar (hampir 14 poin)
- Kemungkinan besar karena unlucky (missed chances, referee decisions, etc.)
- Regression to mean suggests mereka akan bounce back

**Action:**
- Bet Wolves to WIN next 3-5 matches
- Start small, increase jika winning streak dimulai

---

### Kasus 2: Over 2.5 Goals - Chelsea Match

```bash
python betting_analyzer.py high-scoring EPL 2025 3.0
python betting_analyzer.py predict Chelsea Brighton EPL 2025
```

**Data:**
- Chelsea: xG 1.89, xGA 1.48 (Total: 3.37)
- Brighton: xG 1.57, xGA 1.62 (Total: 3.20)

**Analysis:**
- Kedua tim high scoring teams
- Total expected: ~3.4 + 3.2 = 6+ goals involvement
- Head-to-head prediction likely > 2.5 goals

**Action:**
- Bet OVER 2.5 goals (High confidence)
- Consider BTTS YES also

---

### Kasus 3: BTTS - Barcelona Match

```bash
python betting_analyzer.py btts La_liga 2025
```

**Data:**
- Barcelona: xG 2.66, xGA 1.49
- Score: 2.08 (HIGH confidence)

**Analysis:**
- Barcelona cetak banyak gol (xG 2.66)
- Tapi juga kebobolan (xGA 1.49)
- Perfect candidate untuk BTTS YES

**Action:**
- Bet BTTS YES ketika Barcelona main
- Especially vs attacking teams

---

## 🔄 Update Data

Update data secara berkala untuk akurasi:

```bash
# Update all leagues
python main.py

# Verify data
python db_utils.py summary 2025
```

**Rekomendasi:**
- Update setiap minggu (setelah matchday selesai)
- Data lebih fresh = prediction lebih akurat

---

## 📞 Quick Reference

```bash
# Match Prediction
python betting_analyzer.py predict <home> <away> <league>

# Find Value Bets
python betting_analyzer.py value-bets 2025 5.0

# High Scoring Teams
python betting_analyzer.py high-scoring EPL 2025

# Low Scoring Teams
python betting_analyzer.py low-scoring RFPL 2025

# BTTS Analysis
python betting_analyzer.py btts La_liga 2025

# Compare Teams
python betting_analyzer.py compare "Team A" "Team B" EPL 2025

# Database Summary
python db_utils.py summary 2025
python db_utils.py table EPL 2025
python db_utils.py top-xg 10 2025
python db_utils.py top-defense 10 2025
```

---

## 🎯 Kesimpulan

**Tools betting yang baik harus:**

1. ✅ **Berbasis Data** - Gunakan xG, xGA, xPTS (bukan feeling)
2. ✅ **Multi-angle Analysis** - Value bets, over/under, BTTS, handicap
3. ✅ **Confidence Scoring** - Tahu mana bet HIGH vs LOW confidence
4. ✅ **Regression to Mean** - Exploit gap antara expected vs actual
5. ✅ **Easy to Use** - Simple CLI commands
6. ✅ **Updated Regular** - Data fresh = better predictions

**Happy Betting! 🎰💰**
