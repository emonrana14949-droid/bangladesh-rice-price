"""
Bangladesh Rice Price Analysis — coarse rice, retail price (BDT/kg).
Real data: WFP Food Prices for Bangladesh, via Humanitarian Data Exchange (HDX).
Source file: data/wfp_food_prices_bgd.csv
Source URL: https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh
Dataset page: https://data.humdata.org/dataset/c76eabb7-fdb5-43b7-a5c4-09091bb8acde
Original collectors: FAO GIEWS / FPMA and Bangladesh Department of
Agricultural Marketing (DAM), via WFP Market Data Collection.
Licence: CC BY-IGO.

What this script does:
1. Loads the raw WFP file (34,490 rows, all foods, 1998-2026).
2. Keeps only "Rice (coarse)", Retail, KG, BDT — the everyday coarse rice
   ordinary families buy. That is 3,695 market-month rows.
3. Builds ONE monthly national series: the mean price across all reporting
   markets in that month (Jan 2004 – Jul 2026, 271 months).
4. EDA: trend, yearly means, year-on-year change, seasonal (calendar-month)
   pattern, distribution, volatility (monthly % change).
5. Forecast test: train on data up to Jul 2025, test on the last 12 months
   (Aug 2025 – Jul 2026). Three honest baselines: seasonal naive
   (same month last year), linear trend, Random Forest on lag features.
   Reports MAE and RMSE for each — no cherry-picking.
6. Saves 7 charts to outputs/ and a plain-text summary to outputs/results.txt.
   Also saves the cleaned monthly series to data/rice_coarse_monthly.csv.

Run:  python analysis.py   (from the project folder)
Needs: pandas, numpy, matplotlib, scikit-learn
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data", "wfp_food_prices_bgd.csv")
OUT = os.path.join(BASE, "outputs")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"font.size": 10, "figure.dpi": 120})


def main():
    raw = pd.read_csv(DATA, parse_dates=["date"])
    print(f"Raw WFP file: {len(raw):,} rows, "
          f"{raw['date'].min().date()} to {raw['date'].max().date()}")

    # --- Keep only coarse rice, retail, per kg -------------------------
    rice = raw[
        (raw["commodity"] == "Rice (coarse)")
        & (raw["pricetype"] == "Retail")
        & (raw["unit"] == "KG")
        & (raw["currency"] == "BDT")
    ].copy()
    rice = rice.dropna(subset=["price"])
    print(f"Rice (coarse), retail, BDT/kg: {len(rice):,} market-month rows, "
          f"{rice['date'].min().date()} to {rice['date'].max().date()}, "
          f"{rice['market'].nunique()} markets, "
          f"{rice['admin1'].nunique()} divisions")

    # --- Monthly national mean (mean across reporting markets) ---------
    # Raw dates are the 15th of each month; normalise to the 1st first.
    rice["month_start"] = rice["date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        rice.groupby("month_start")["price"]
        .agg(["mean", "count", "min", "max", "std"])
        .rename(columns={"mean": "price", "count": "n_markets"})
        .reset_index()
        .rename(columns={"month_start": "date"})
        .sort_values("date")
    )
    monthly["date"] = pd.to_datetime(monthly["date"])
    monthly = monthly.set_index("date").asfreq("MS")
    # asfreq creates NaN rows for any missing month; count them honestly
    missing_months = int(monthly["price"].isna().sum())
    monthly["price"] = monthly["price"].interpolate(limit_direction="both")
    monthly["year"] = monthly.index.year
    monthly["month"] = monthly.index.month
    monthly["month_name"] = monthly.index.strftime("%b")
    monthly["pct_change"] = monthly["price"].pct_change() * 100
    monthly["yoy"] = monthly["price"].pct_change(12) * 100
    monthly["roll12"] = monthly["price"].rolling(12).mean()
    monthly["roll_vol"] = monthly["pct_change"].rolling(12).std()

    monthly.to_csv(os.path.join(BASE, "data", "rice_coarse_monthly.csv"))
    n_months = len(monthly)
    first, last = monthly.index.min(), monthly.index.max()

    # --- Summary stats --------------------------------------------------
    price = monthly["price"]
    stats = {
        "n_market_rows": int(len(rice)),
        "n_months": int(n_months),
        "first_month": str(first.date()),
        "last_month": str(last.date()),
        "missing_months_filled": missing_months,
        "n_markets_total": int(rice["market"].nunique()),
        "mean_price": float(price.mean()),
        "median_price": float(price.median()),
        "min_price": float(price.min()),
        "min_month": str(price.idxmin().date()),
        "max_price": float(price.max()),
        "max_month": str(price.idxmax().date()),
        "std_price": float(price.std()),
        "first_price": float(price.iloc[0]),
        "last_price": float(price.iloc[-1]),
        "total_change_pct": float((price.iloc[-1] / price.iloc[0] - 1) * 100),
        "mean_monthly_pct_change": float(monthly["pct_change"].mean()),
        "std_monthly_pct_change": float(monthly["pct_change"].std()),
        "mean_yoy_pct": float(monthly["yoy"].mean()),
    }
    # Year-on-year for the last full year in the data (Jul 2025 -> Jul 2026)
    stats["last_yoy_pct"] = float(monthly["yoy"].iloc[-1])

    yearly = monthly.groupby("year")["price"].mean()
    yearly_change = yearly.pct_change() * 100
    best_year = yearly.idxmax()
    worst_year = yearly.idxmin()

    seasonal = monthly.groupby("month")["price"].mean()
    seasonal.index = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    cheapest_month = seasonal.idxmin()
    dearest_month = seasonal.idxmax()

    # Division comparison (mean retail price of coarse rice, whole period)
    division = rice.groupby("admin1")["price"].agg(["mean", "count"]).sort_values("mean")

    # --- Forecast test: last 12 months ---------------------------------
    # Features: lag 1, 3, 6, 12 months, month number, time trend.
    df = monthly[["price"]].copy()
    df["lag1"] = df["price"].shift(1)
    df["lag3"] = df["price"].shift(3)
    df["lag6"] = df["price"].shift(6)
    df["lag12"] = df["price"].shift(12)
    df["month"] = df.index.month
    df["t"] = np.arange(len(df))
    df = df.dropna()

    test_n = 12
    train, test = df.iloc[:-test_n], df.iloc[-test_n:]
    feats = ["lag1", "lag3", "lag6", "lag12", "month", "t"]

    # 1) Seasonal naive: same month last year
    pred_naive = test["lag12"].values
    # 2) Linear trend on time only
    lin = LinearRegression().fit(train[["t"]], train["price"])
    pred_lin = lin.predict(test[["t"]])
    # 3) Random Forest on lag features
    rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    rf.fit(train[feats], train["price"])
    pred_rf = rf.predict(test[feats])

    def scores(actual, pred):
        return {
            "mae": float(mean_absolute_error(actual, pred)),
            "rmse": float(np.sqrt(mean_squared_error(actual, pred))),
        }

    fc = {
        "test_period": f"{test.index.min().date()} to {test.index.max().date()}",
        "seasonal_naive": scores(test["price"], pred_naive),
        "linear_trend": scores(test["price"], pred_lin),
        "random_forest": scores(test["price"], pred_rf),
        "test_mean_price": float(test["price"].mean()),
    }
    best_model = min(fc, key=lambda k: fc[k]["mae"] if k in
                     ("seasonal_naive", "linear_trend", "random_forest") else 1e9)

    # --- Charts ----------------------------------------------------------
    # 1. Price trend over time
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(monthly.index, monthly["price"], color="#2E7D32", lw=1.2,
            label="Monthly national mean (BDT/kg)")
    ax.plot(monthly.index, monthly["roll12"], color="#C62828", lw=2,
            label="12-month rolling mean")
    ax.set_title("Coarse rice retail price in Bangladesh, 2004–2026 (BDT per kg)")
    ax.set_xlabel("Year")
    ax.set_ylabel("BDT / kg")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "01_price_trend.png"))
    plt.close(fig)

    # 2. Monthly (seasonal) average
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(seasonal.index, seasonal.values, color="#1565C0")
    ax.set_title("Average coarse rice price by calendar month (2004–2026)")
    ax.set_xlabel("Month")
    ax.set_ylabel("Mean price (BDT / kg)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "02_monthly_average.png"))
    plt.close(fig)

    # 3. Yearly comparison
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar(yearly.index.astype(str), yearly.values, color="#6A1B9A")
    ax.set_title("Average coarse rice price by year (BDT per kg)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean price (BDT / kg)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "03_yearly_comparison.png"))
    plt.close(fig)

    # 4. Price distribution
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(price.values, bins=30, color="#00897B", edgecolor="white")
    ax.axvline(price.mean(), color="#C62828", lw=2,
               label=f"Mean {price.mean():.1f} BDT/kg")
    ax.axvline(price.median(), color="#333333", lw=2, ls="--",
               label=f"Median {price.median():.1f} BDT/kg")
    ax.set_title("Distribution of monthly coarse rice prices (2004–2026)")
    ax.set_xlabel("Price (BDT / kg)")
    ax.set_ylabel("Number of months")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "04_price_distribution.png"))
    plt.close(fig)

    # 5. Volatility — monthly % change and rolling volatility
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(monthly.index, monthly["pct_change"], color="#EF6C00", lw=0.9,
            label="Month-on-month % change")
    ax.plot(monthly.index, monthly["roll_vol"], color="#283593", lw=2,
            label="12-month rolling std of % change")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_title("How jumpy is the rice price? Monthly % change and volatility")
    ax.set_xlabel("Year")
    ax.set_ylabel("% change")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "05_volatility.png"))
    plt.close(fig)

    # 6. Forecast vs actual (last 12 months)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(test.index, test["price"], "o-", color="black", lw=2,
            label="Actual")
    ax.plot(test.index, pred_naive, "s--", color="#1565C0",
            label=f"Seasonal naive (MAE {fc['seasonal_naive']['mae']:.2f})")
    ax.plot(test.index, pred_lin, "^-.", color="#C62828",
            label=f"Linear trend (MAE {fc['linear_trend']['mae']:.2f})")
    ax.plot(test.index, pred_rf, "d:", color="#2E7D32",
            label=f"Random Forest (MAE {fc['random_forest']['mae']:.2f})")
    ax.set_title(f"Next-month price forecast test, {fc['test_period']} (BDT / kg)")
    ax.set_xlabel("Month")
    ax.set_ylabel("BDT / kg")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "06_forecast_vs_actual.png"))
    plt.close(fig)

    # 7. Division comparison
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(division.index, division["mean"].values, color="#5D4037")
    ax.set_title("Average coarse rice price by division (2004–2026, BDT / kg)")
    ax.set_xlabel("Mean price (BDT / kg)")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "07_division_comparison.png"))
    plt.close(fig)

    # --- Results file ----------------------------------------------------
    lines = []
    lines.append("BANGLADESH RICE PRICE ANALYSIS — RESULTS")
    lines.append("Coarse rice, retail, BDT per kg")
    lines.append("Source: WFP Food Prices for Bangladesh (HDX), "
                 "https://data.humdata.org/dataset/wfp-food-prices-for-bangladesh")
    lines.append("Original collectors: FAO GIEWS / FPMA and Bangladesh "
                 "Department of Agricultural Marketing (DAM). Licence: CC BY-IGO.")
    lines.append("")
    lines.append(f"Raw file: {len(raw):,} rows, all foods, "
                 f"{raw['date'].min().date()} to {raw['date'].max().date()}")
    lines.append(f"Rice (coarse) retail rows used: {stats['n_market_rows']:,}")
    lines.append(f"Monthly national series: {stats['n_months']} months, "
                 f"{stats['first_month']} to {stats['last_month']}")
    lines.append(f"Markets in the rice data: {stats['n_markets_total']} "
                 f"(number reporting each month varies; see data file)")
    lines.append(f"Missing months filled by interpolation: {missing_months}")
    lines.append("")
    lines.append("KEY NUMBERS (monthly national mean, BDT/kg)")
    lines.append(f"  Mean price:   {stats['mean_price']:.2f}")
    lines.append(f"  Median price: {stats['median_price']:.2f}")
    lines.append(f"  Std dev:      {stats['std_price']:.2f}")
    lines.append(f"  Lowest month: {stats['min_price']:.2f} in {stats['min_month']}")
    lines.append(f"  Highest month:{stats['max_price']:.2f} in {stats['max_month']}")
    lines.append(f"  First month ({stats['first_month']}): {stats['first_price']:.2f}")
    lines.append(f"  Last month  ({stats['last_month']}): {stats['last_price']:.2f}")
    lines.append(f"  Total change first to last month: {stats['total_change_pct']:+.1f}%")
    lines.append(f"  Mean month-on-month change: {stats['mean_monthly_pct_change']:+.2f}% "
                 f"(std {stats['std_monthly_pct_change']:.2f}%)")
    lines.append(f"  Mean year-on-year change: {stats['mean_yoy_pct']:+.2f}%")
    lines.append(f"  Year-on-year change, last month: {stats['last_yoy_pct']:+.2f}%")
    lines.append("")
    lines.append("YEARLY MEANS (BDT/kg) AND YEAR-ON-YEAR CHANGE")
    for y in yearly.index:
        ch = yearly_change.get(y, np.nan)
        ch_s = f"{ch:+.1f}%" if pd.notna(ch) else "  —  "
        lines.append(f"  {y}: {yearly[y]:6.2f}   YoY {ch_s}")
    lines.append(f"  Cheapest year on average: {worst_year} ({yearly[worst_year]:.2f})")
    lines.append(f"  Dearest year on average:  {best_year} ({yearly[best_year]:.2f})")
    lines.append("")
    lines.append("SEASONAL PATTERN (mean price by calendar month, BDT/kg)")
    for m, v in seasonal.items():
        lines.append(f"  {m}: {v:.2f}")
    lines.append(f"  Cheapest month on average: {cheapest_month} ({seasonal[cheapest_month]:.2f})")
    lines.append(f"  Dearest month on average:  {dearest_month} ({seasonal[dearest_month]:.2f})")
    lines.append(f"  Seasonal gap (dearest - cheapest): "
                 f"{seasonal.max() - seasonal.min():.2f} BDT/kg")
    lines.append("")
    lines.append("DIVISION MEANS (BDT/kg, whole period)")
    for div, row in division.iterrows():
        lines.append(f"  {div}: {row['mean']:.2f}  (n={int(row['count'])})")
    lines.append("")
    lines.append(f"FORECAST TEST — last 12 months ({fc['test_period']}), "
                 f"test mean price {fc['test_mean_price']:.2f} BDT/kg")
    for name in ("seasonal_naive", "linear_trend", "random_forest"):
        lines.append(f"  {name:15s} MAE {fc[name]['mae']:.2f} BDT/kg, "
                     f"RMSE {fc[name]['rmse']:.2f} BDT/kg")
    lines.append(f"  Best on MAE in this test: {best_model} "
                 f"(MAE {fc[best_model]['mae']:.2f} BDT/kg)")
    lines.append("  Note: these are simple baselines on a 12-month test only. "
                 "They are NOT a promise about next month's price.")
    lines.append("")
    lines.append("LIMITATIONS")
    lines.append("  - The monthly series is a mean across all markets that reported "
                 "in that month; the number of reporting markets changes over time, "
                 "so early years rest on fewer markets.")
    lines.append("  - Only coarse rice, retail, BDT/kg is analysed. Fine/medium rice, "
                 "wholesale prices and paddy prices are in the raw file but not used here.")
    lines.append("  - Prices are nominal BDT — they are NOT adjusted for inflation, "
                 "so part of the long rise is general price inflation.")
    lines.append("  - The forecast test is only 12 months; a longer test would be "
                 "needed before trusting any model.")
    lines.append("  - WFP/HDX data can be revised after publication; re-download "
                 "the file to get the newest version.")

    with open(os.path.join(OUT, "results.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print("\nCharts saved to outputs/ (7 PNGs).")
    return stats, fc


if __name__ == "__main__":
    main()
