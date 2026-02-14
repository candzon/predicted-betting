# 📁 Struktur Project

```
predicted-betting/
├── 📂 src/                    # Source code utama
│   ├── understat_scraper.py   # Scraper untuk Understat.com
│   ├── betting_analyzer.py    # Analisis betting
│   ├── ucl_analyzer.py        # Analisis UCL
│   ├── scraper_uefa.py        # Scraper UEFA
│   └── db_utils.py            # Database utilities
│
├── 📂 docs/                   # Dokumentasi lengkap
│   ├── GUIDE.md               # Panduan penggunaan
│   ├── BETTING_GUIDE.md       # Panduan betting
│   ├── BETTING_SUMMARY.md     # Summary betting
│   ├── ADVANCED_STATS_GUIDE.md # Panduan stats lanjutan
│   └── PROJECT_SUMMARY.md     # Summary project
│
├── 📂 config/                 # File konfigurasi
│   ├── schema.prisma          # Database schema
│   └── .gitignore             # Git ignore rules
│
├── 📂 data/                   # Database dan data files
│   └── betting_analysis.db    # SQLite database
│
├── 📄 main.py                 # Entry point utama
├── 📄 setup.py                # Setup script
├── 📄 requirements.txt        # Dependencies
├── 📄 README.md               # Dokumentasi utama
└── 📄 schema.prisma           # Copy untuk Prisma client

```

## 🚀 Cara Menggunakan

```bash
# Install dependencies
pip install -r requirements.txt

# Generate Prisma client
prisma generate

# Push database schema
prisma db push

# Run scraper
python main.py
```

## 📖 Dokumentasi

Lihat folder `docs/` untuk dokumentasi lengkap:
- **GUIDE.md** - Panduan penggunaan lengkap
- **BETTING_GUIDE.md** - Strategi dan analisis betting
- **ADVANCED_STATS_GUIDE.md** - Penjelasan statistik lanjutan
