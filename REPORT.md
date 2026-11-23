# Bangladesh Rice Price Analysis — Report

**Coarse rice, retail price, BDT per kg — Jan 2004 to Jul 2026**
Md. Emon Rana, BSc in CSE (final year), Southeast University, Dhaka
Date of analysis: 23 November 2026

## 1. Introduction

Rice is the main food of Bangladesh. Coarse rice is the grade most ordinary
families buy, so its price decides how much of a family's money goes to food.
This project asks three simple questions with real data:

1. How has the price of coarse rice changed from 2004 to 2026?
2. Is there a season when rice is cheaper or dearer?
3. Can a simple model guess next month's price — and how wrong is it?

No price in this report is invented. Every number comes from the dataset
named in Section 2, and the code that made every number is in
`analysis.py` (and the same steps in `analysis.ipynb`).

## 2. Data

- **Source:** WFP Food Prices for Bangladesh, Humanitarian Data Exchange (HDX) —
  https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh
- **Original collectors:** FAO GIEWS / FPMA and Bangladesh Department of
  Agricultural Marketing (DAM), via WFP Market Data Collection. Licence: CC BY-IGO.
- **Raw file:** `data/wfp_food_prices_bgd.csv` — 34,490 rows, all foods,
  15 Jul 1998 – 15 Sep 2026. Columns include date, market, division
  (`admin1`), commodity, price type (Retail/Wholesale), unit, currency,
  price and USD price.
- **What was used:** only `commodity = "Rice (coarse)"`, `pricetype = Retail`,
  `unit = KG`, `currency = BDT` — **3,695 market-month rows**, 86 markets,
  8 divisions, 15 Jan 2004 – 15 Jul 2026. No missing prices in these rows.
- **Monthly series built:** for each month, the mean price across all markets
  that reported that month. That gives **271 months** (Jan 2004 – Jul 2026),
  saved as `data/rice_coarse_monthly.csv`. Four months had no reporting market
  at all (Jul–Aug 2019, Nov 2025, Jan 2026) and were filled by linear
  interpolation between the neighbouring months; this is stated here, not hidden.

A warning about coverage: the number of reporting markets changes a lot over
time. In 2004–2006 only 1–5 markets reported per month (mostly Dhaka
Division); in 2007–2019 it was about 6 markets; from 2020 it rose to
24–65 markets (median 24 in 2020, 57 in 2024). So the monthly mean of the
early years rests on very few markets, while recent years rest on many.
The long trend is still clear, but early-year values should be read with
that in mind.

## 3. Method

1. **Load and filter** the raw WFP file to coarse rice, retail, BDT/kg.
2. **Monthly national mean** across reporting markets (see Section 2).
3. **EDA:** mean/median/min/max, month-on-month % change, year-on-year
   % change, yearly means, calendar-month (seasonal) means, distribution,
   12-month rolling mean and rolling volatility, division means.
4. **Forecast test:** train on data up to Jul 2025, test on the last
   12 months (Aug 2025 – Jul 2026). Three models:
   - *Seasonal naive* — predict the price of the same month last year.
   - *Linear trend* — a straight line fitted on time, extended forward.
   - *Random Forest* — 300 trees, features: price 1, 3, 6 and 12 months
     ago, calendar month, and a time index.
   Error is reported as MAE and RMSE in BDT/kg for all three models.
5. All charts are made with matplotlib; all numbers are saved in
   `outputs/results.txt`.

Prices are **nominal BDT** — they are not adjusted for inflation.

## 4. Results

### 4.1 The long rise

| Measure | Value (BDT/kg) |
|---|---|
| Mean monthly price, 2004–2026 | 32.86 |
| Median | 31.60 |
| Standard deviation | 10.89 |
| Lowest month | 14.00 — Jan 2004 |
| Highest month | 53.49 — Jul 2025 |
| First month (Jan 2004) | 14.00 |
| Last month (Jul 2026) | 49.31 |
| Change, first to last month | **+252.2%** |

Coarse rice cost about 14 BDT/kg in early 2004 and about 49 BDT/kg in
Jul 2026. The rise was not smooth: the price jumped +41.8% in 2007 and
+28.5% in 2008 (the world food-price crisis years), fell −29.1% in 2009,
jumped again +35.2% in 2010, and rose steadily from 2020 (37.45) to 2025
(52.74). The mean month-on-month change over the whole period is +0.65%
(std 6.48%); the mean year-on-year change is +8.21%.

Yearly means (BDT/kg): 2004: 14.66, 2005: 16.58, 2006: 16.75,
2007: 23.75, 2008: 30.51, 2009: 21.63, 2010: 29.25, 2011: 31.97,
2012: 26.26, 2013: 30.01, 2014: 33.38, 2015: 29.00, 2016: 29.27,
2017: 37.38, 2018: 37.35, 2019: 29.92, 2020: 37.45, 2021: 43.63,
2022: 44.89, 2023: 46.37, 2024: 50.22, 2025: 52.74, 2026: 50.10
(2026 covers Jan–Jul only). Cheapest year on average: 2004. Dearest year
on average: 2025.

The most recent turn is down, not up: the year-on-year change in
Jul 2026 was **−7.82%** — the price in Jul 2026 (49.31) was lower than
in Jul 2025 (53.49).

### 4.2 Almost no seasonal pattern

Mean price by calendar month (BDT/kg): Jan 32.57, Feb 33.08, Mar 33.01,
Apr 32.41, May 32.68, Jun 32.73, Jul 33.23, Aug 32.79, Sep 32.73,
Oct 32.95, Nov 32.97, Dec 33.23.

Cheapest month on average is April (32.41) and dearest is July (33.23) —
a gap of only **0.82 BDT/kg**. In plain words: over 2004–2026, the month
of the year barely mattered for the national mean price of coarse rice.
The big moves are year-to-year, not month-to-month. (This is a finding,
not a failure of the analysis — it is what the data says.)

### 4.3 Volatility

Month-on-month changes are usually small (mean +0.65%) but sometimes
large: the standard deviation of monthly % change is 6.48%, and the
biggest swings sit around the 2007–2010 crisis years (see
`outputs/05_volatility.png`). In recent years (2024–2026) the rolling
volatility is around 1.1–1.3%, much calmer than in the crisis years.

### 4.4 Price by division (descriptive only)

Mean coarse-rice price over the whole period (BDT/kg): Sylhet 38.77
(n=317), Rajshahi 40.14 (n=501), Barisal 41.59 (n=377), Khulna 42.54
(n=682), Chittagong 42.67 (n=584), Dhaka 43.76 (n=778), Rangpur 45.39
(n=281), Mymensingh 46.55 (n=175).

This must not be read as "rice is cheapest in Sylhet today": divisions
reported in different years, and prices were much lower in the early
years when only some divisions reported. It is a description of the
pooled data, not a fair like-for-like comparison.

### 4.5 Forecast test (Aug 2025 – Jul 2026)

Test mean price: 51.04 BDT/kg.

| Model | MAE (BDT/kg) | RMSE (BDT/kg) |
|---|---:|---:|
| Seasonal naive | 2.34 | 2.58 |
| Linear trend | 2.30 | 2.88 |
| **Random Forest** | **1.47** | **1.68** |

Random Forest had the smallest error in this test — on average it was
off by 1.47 BDT/kg, about 2.9% of the test mean price. That is a decent
result for such a simple model, but the test is only 12 months long, and
the test period was a falling-price period (from 53.41 in Aug 2025 to
49.31 in Jul 2026), which flatters models that follow recent lags.
A longer test, and a test over a rising-price period, would be needed
before trusting any of these models.

## 5. Limitations

- **Changing market coverage** (Section 2): early years rest on 1–6 markets, recent years on 27–65. The monthly mean is not built from the same markets every month.
- **4 interpolated months** (Jul–Aug 2019, Nov 2025, Jan 2026) have no real observation behind them.
- **Only coarse rice, retail, BDT/kg.** Fine/medium rice, wholesale prices and paddy prices are in the raw file but not analysed here.
- **Nominal prices, not inflation-adjusted.** Part of the +252% rise since 2004 is general inflation, not rice getting scarcer.
- **Forecast test is 12 months only.** Do not use these models to bet on next month's price.
- **Division comparison is not like-for-like** (Section 4.4).
- **Data can be revised:** WFP/HDX updates this file; re-download it for the newest version. The analysis was run on the file downloaded 23 Nov 2026 (last modified on HDX 4 Nov 2026; dataset date range to 15 Sep 2026).

## 6. Conclusion

With real market data, the story of coarse rice in Bangladesh is a story
of a long rise with sharp jumps — 14 BDT/kg in 2004 to about 49 BDT/kg
in mid-2026 — followed by a fall in the last year of the data. There is
almost no seasonal pattern in the national mean, and a simple
Random Forest on past prices guessed the last 12 months with an average
error of 1.47 BDT/kg. The honest limits above matter as much as the
headline numbers: the early years rest on few markets, prices are not
inflation-adjusted, and a 12-month forecast test is short.

## Files

- `analysis.py` — the full analysis as a script
- `analysis.ipynb` — the same analysis as a Jupyter notebook (executed, all cells run, no errors)
- `data/wfp_food_prices_bgd.csv` — raw WFP/HDX data (34,490 rows)
- `data/rice_coarse_monthly.csv` — clean monthly national series (271 months)
- `outputs/` — 7 charts (`01`–`07`) and `outputs/results.txt`
- `requirements.txt` — Python packages needed
