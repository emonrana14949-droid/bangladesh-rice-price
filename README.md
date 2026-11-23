# Bangladesh Rice Price Analysis 🍚

**How much does coarse rice cost in Bangladesh — and where is the price going?**

I am Md. Emon Rana, a final-year CSE student at Southeast University, Dhaka.
Coarse rice is the rice most families in Bangladesh eat every day, so I wanted to see
its real price story with real data — not guesses.

## What I found (short version)

| Fact | Value |
|---|---|
| Data | Coarse rice, retail, BDT/kg, Jan 2004 – Jul 2026 |
| Rows used | 3,695 market-month rows, 86 markets, 8 divisions |
| Mean price | **32.86 BDT/kg** (median 31.60) |
| Cheapest month | **14.00 BDT/kg — Jan 2004** |
| Dearest month | **53.49 BDT/kg — Jul 2025** |
| First → last month | 14.00 → 49.31 BDT/kg (**+252.2%**) |
| Dearest year on average | **2025 — 52.74 BDT/kg** |
| Price fell last year | Jul 2026 was **−7.82%** vs Jul 2025 |
| Seasonal gap | Only **0.82 BDT/kg** between cheapest (Apr) and dearest (Jul) month |
| Best forecast (12-month test) | Random Forest, **MAE 1.47 BDT/kg** |

> Prices are nominal taka — **not** adjusted for inflation, so part of the long rise is general inflation. The forecast is a 12-month test only, not a promise about next month.

## Data — real, with the source

- **Dataset:** WFP Food Prices for Bangladesh, Humanitarian Data Exchange (HDX)
- **Link:** https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh
- **Original collectors:** FAO GIEWS / FPMA and Bangladesh Department of Agricultural Marketing (DAM), via WFP Market Data Collection
- **Licence:** CC BY-IGO
- **Raw file in this repo:** `data/wfp_food_prices_bgd.csv` — 34,490 rows, all foods, 15 Jul 1998 – 15 Sep 2026
- **What I used:** only `Rice (coarse)`, Retail, KG, BDT — 3,695 rows, Jan 2004 – Jul 2026
- **Clean monthly series I built:** `data/rice_coarse_monthly.csv` — 271 months, national mean across reporting markets

## How to run

```bash
# 1. Make a virtual environment and install what is needed
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux
pip install -r requirements.txt

# 2. Run the script (same work as the notebook)
python analysis.py

# 3. Or open the notebook in Jupyter
jupyter notebook analysis.ipynb
# or: jupyter lab analysis.ipynb
```

`analysis.py` and `analysis.ipynb` do the same work: load → clean → monthly series →
EDA → forecast test → 7 charts in `outputs/` + `outputs/results.txt`.

## Charts

| Chart | What it shows |
|---|---|
| `01_price_trend.png` | Monthly price + 12-month rolling mean, 2004–2026 |
| `02_monthly_average.png` | Mean price by calendar month (seasonal pattern) |
| `03_yearly_comparison.png` | Mean price by year |
| `04_price_distribution.png` | Distribution of monthly prices |
| `05_volatility.png` | Month-on-month % change and rolling volatility |
| `06_forecast_vs_actual.png` | Forecast test, Aug 2025 – Jul 2026 |
| `07_division_comparison.png` | Mean price by division |

## Forecast test (honest numbers)

Tested on the last 12 months (Aug 2025 – Jul 2026), trained on everything before:

| Model | MAE (BDT/kg) | RMSE (BDT/kg) |
|---|---:|---:|
| Seasonal naive (same month last year) | 2.34 | 2.58 |
| Linear trend | 2.30 | 2.88 |
| **Random Forest (lags 1, 3, 6, 12 + month + time)** | **1.47** | **1.68** |

Random Forest won this short test — but 12 months is a short test, so I do not claim it will always win.

## Limits — read these, please

- The monthly price is a mean of the markets that reported that month. In 2004 only **1 market** reported most months; in 2024 it was 41–65 markets. Early years are weaker than recent years.
- **4 months had no data at all** (Jul–Aug 2019, Nov 2025, Jan 2026) and were filled by straight-line interpolation between the months around them.
- Only coarse rice, retail, BDT/kg. Fine/medium rice, wholesale and paddy prices are in the raw file but not used here.
- Prices are nominal BDT, not inflation-adjusted.
- The division comparison is descriptive only — divisions reported in different years, so it is not a fair like-for-like comparison.
- WFP/HDX data can be revised later — re-download the file for the newest version.

Full write-up: [`REPORT.md`](REPORT.md). Full numbers: [`outputs/results.txt`](outputs/results.txt).
