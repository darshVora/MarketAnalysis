"""
Hypothesis Test: Does Earnings Growth Translate Into Long-Term Price Appreciation
              ONLY When the Stock Is Bought at a Reasonable Valuation (Trailing P/E)?

Methodology
-----------
For each quarterly earnings event in earnings_valuation_data.parquet:
  - Growth signal  : profit_yoy_growth (YoY net profit change)
  - Valuation gate : trailing_pe (stock price / TTM EPS at time of filing)
  - Outcome        : forward_3yr_% and forward_5yr_% (3- and 5-year price return)

We answer two questions:
  Q1. Does high earnings growth alone predict long-term outperformance?
  Q2. Does buying high-growth companies at a LOW P/E generate significantly
      better 3-5 year returns than buying the SAME growth at a HIGH P/E?

Statistical tests used:
  - Kruskal-Wallis  : non-parametric ANOVA across all P/E buckets
  - Mann-Whitney U  : pairwise test  cheap vs. expensive within top-growth stocks
  - Cohen's d       : effect size to judge practical significance
"""

import polars as pl
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class _Tee:
    """Write to both stdout and a file simultaneously."""
    def __init__(self, file):
        self._file = file
        self._stdout = sys.stdout
    def write(self, data):
        self._stdout.write(data)
        self._file.write(data)
    def flush(self):
        self._stdout.flush()
        self._file.flush()

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")
DATA_PATH = os.path.join(_DATA_DIR, "earnings_valuation_data.parquet")

# ── P/E bucket thresholds (absolute, not sector-relative) ──────────────────────
PE_BINS   = [0, 10, 15, 25, 40, np.inf]
PE_LABELS = ['<10 (Deep Value)', '10-15 (Value)', '15-25 (Fair)', '25-40 (Premium)', '>40 (Expensive)']

# ── Growth quartile labels ─────────────────────────────────────────────────────
GROWTH_LABELS = ['Q1 (Weak)', 'Q2 (Moderate)', 'Q3 (Good)', 'Q4 (Strong)']


def cohens_d(a, b):
    """Effect size between two groups."""
    pooled_std = np.sqrt((np.std(a, ddof=1)**2 + np.std(b, ddof=1)**2) / 2)
    return (np.mean(a) - np.mean(b)) / pooled_std if pooled_std > 0 else 0.0


def load_and_clean() -> pd.DataFrame:
    df = pl.read_parquet(DATA_PATH).to_pandas()
    df.sort_values('event_date', inplace=True)

    # Clip runaway growth ratios (turnarounds from near-zero base)
    df = df[(df['profit_yoy_growth'].between(-10, 10))]
    df = df[(df['rev_yoy_growth'].between(-5, 5))]

    # Keep only profitable companies (positive TTM EPS ⟹ positive P/E)
    df = df[df['trailing_pe'].notna() & (df['trailing_pe'] > 0) & (df['trailing_pe'] < 150)]

    print(f"Events after cleaning          : {len(df):,}")
    print(f"  with 3-year return available : {df['forward_3yr_%'].notna().sum():,}")
    print(f"  with 5-year return available : {df['forward_5yr_%'].notna().sum():,}")
    print(f"  date range                   : {df['event_date'].min().date()} → {df['event_date'].max().date()}\n")

    return df


def assign_buckets(df: pd.DataFrame) -> pd.DataFrame:
    # Valuation buckets (absolute P/E)
    df['pe_bucket'] = pd.cut(df['trailing_pe'], bins=PE_BINS, labels=PE_LABELS)

    # Growth quartiles (relative to full dataset)
    df['growth_quartile'] = pd.qcut(df['profit_yoy_growth'], q=4, labels=GROWTH_LABELS, duplicates='drop')

    return df


def bucket_return_matrix(df: pd.DataFrame, return_col: str):
    """Print median returns for every (growth quartile × P/E bucket) cell."""
    print(f"\n{'═'*70}")
    print(f"  Median {return_col} by Growth Quartile × Trailing P/E Bucket")
    print(f"{'═'*70}")

    pivot = (
        df.dropna(subset=[return_col, 'pe_bucket', 'growth_quartile'])
          .groupby(['growth_quartile', 'pe_bucket'], observed=True)[return_col]
          .agg(['median', 'mean', 'count'])
          .rename(columns={'median': 'Median %', 'mean': 'Mean %', 'count': 'N'})
          .reset_index()
    )
    pivot['Median %'] = pivot['Median %'].map('{:+.1f}%'.format)
    pivot['Mean %']   = pivot['Mean %'].map('{:+.1f}%'.format)
    print(pivot.to_string(index=False))


def hypothesis_test_cheap_vs_expensive(df: pd.DataFrame, return_col: str):
    """
    Within the TOP growth quartile, compare returns for cheap P/E vs. expensive P/E stocks.
    Hypothesis H1: cheap (PE < 15) outperforms expensive (PE > 25) over 3-5 years.
    """
    horizon_label = return_col.replace('forward_', '').replace('_%', '')
    print(f"\n{'─'*70}")
    print(f"  Hypothesis Test ({horizon_label} horizon) — Top-Growth Quartile Only")
    print(f"  H0: Median returns are equal regardless of entry valuation")
    print(f"  H1: Cheap P/E stocks deliver HIGHER long-term returns")
    print(f"{'─'*70}")

    top_growth = df[df['growth_quartile'] == 'Q4 (Strong)'].dropna(subset=[return_col])
    if len(top_growth) < 20:
        print("  Insufficient data for test.\n")
        return

    cheap     = top_growth[top_growth['trailing_pe'] < 15][return_col].dropna().values
    fair      = top_growth[top_growth['trailing_pe'].between(15, 25)][return_col].dropna().values
    expensive = top_growth[top_growth['trailing_pe'] > 25][return_col].dropna().values

    for label, group in [('Cheap  (PE < 15)', cheap), ('Fair (PE 15-25)', fair), ('Expensive (PE > 25)', expensive)]:
        if len(group) == 0:
            continue
        print(f"  {label:25s} | N={len(group):4d} | Median={np.median(group):+7.1f}% | Mean={np.mean(group):+7.1f}%"
              f" | Std={np.std(group):.1f}%")

    # Mann-Whitney U: cheap vs expensive
    if len(cheap) >= 10 and len(expensive) >= 10:
        stat, p = stats.mannwhitneyu(cheap, expensive, alternative='greater')
        d = cohens_d(cheap, expensive)
        print(f"\n  Mann-Whitney U (cheap > expensive): U={stat:.0f}, p={p:.4f}")
        print(f"  Cohen's d (effect size)           : {d:+.3f}  ", end='')
        if abs(d) >= 0.8:
            print("← LARGE effect")
        elif abs(d) >= 0.5:
            print("← MEDIUM effect")
        elif abs(d) >= 0.2:
            print("← SMALL effect")
        else:
            print("← negligible")
        if p < 0.05:
            print(f"  ✅ RESULT: Statistically significant at 5% level — valuation MATTERS for {horizon_label} returns.")
        else:
            print(f"  ❌ RESULT: Not statistically significant — valuation effect unclear at 5% level.")
    else:
        print("  Not enough observations in cheap/expensive buckets for Mann-Whitney test.")

    # Kruskal-Wallis across all P/E buckets within top growth
    groups = [
        top_growth[top_growth['pe_bucket'] == b][return_col].dropna().values
        for b in PE_LABELS
    ]
    groups = [g for g in groups if len(g) >= 5]
    if len(groups) >= 2:
        kw_stat, kw_p = stats.kruskal(*groups)
        print(f"\n  Kruskal-Wallis across all P/E buckets: H={kw_stat:.2f}, p={kw_p:.4f}")


def growth_effect_test(df: pd.DataFrame, return_col: str):
    """Test whether high earnings growth alone (ignoring valuation) predicts outperformance."""
    horizon_label = return_col.replace('forward_', '').replace('_%', '')
    print(f"\n{'─'*70}")
    print(f"  Growth Effect Test ({horizon_label}) — All P/E Levels Combined")
    print(f"{'─'*70}")

    top    = df[df['growth_quartile'] == 'Q4 (Strong)'].dropna(subset=[return_col])[return_col].values
    bottom = df[df['growth_quartile'] == 'Q1 (Weak)'].dropna(subset=[return_col])[return_col].values

    if len(top) < 10 or len(bottom) < 10:
        print("  Insufficient data.")
        return

    print(f"  Strong growth (Q4): N={len(top):4d} | Median={np.median(top):+7.1f}% | Mean={np.mean(top):+7.1f}%")
    print(f"  Weak   growth (Q1): N={len(bottom):4d} | Median={np.median(bottom):+7.1f}% | Mean={np.mean(bottom):+7.1f}%")

    stat, p = stats.mannwhitneyu(top, bottom, alternative='greater')
    d = cohens_d(top, bottom)
    print(f"\n  Mann-Whitney U (Q4 > Q1): U={stat:.0f}, p={p:.4f}, Cohen's d={d:+.3f}")
    if p < 0.05:
        print("  ✅ Earnings growth IS a statistically significant predictor of long-term returns.")
    else:
        print("  ❌ Earnings growth alone is NOT a statistically significant predictor.")


def pe_distribution_by_growth(df: pd.DataFrame):
    """Show the P/E distribution across growth quartiles — sanity check."""
    print(f"\n{'─'*70}")
    print("  Trailing P/E Distribution by Growth Quartile")
    print(f"{'─'*70}")
    summary = (
        df.groupby('growth_quartile', observed=True)['trailing_pe']
        .agg(['median', 'mean', 'min', 'max', 'count'])
        .rename(columns={'median': 'Median PE', 'mean': 'Mean PE', 'min': 'Min', 'max': 'Max', 'count': 'N'})
    )
    print(summary.to_string())


def run():
    print("=" * 70)
    print("  HYPOTHESIS: Earnings Growth + Reasonable Valuation → Long-Term Alpha")
    print("=" * 70)
    print()

    df = load_and_clean()
    df = assign_buckets(df)

    pe_distribution_by_growth(df)

    for return_col in ['forward_3yr_%', 'forward_5yr_%']:
        bucket_return_matrix(df, return_col)
        growth_effect_test(df, return_col)
        hypothesis_test_cheap_vs_expensive(df, return_col)

    print(f"\n{'═'*70}")
    print("  SUMMARY")
    print(f"{'═'*70}")
    print("""
  Step 1: Run compile_earnings_dataset.py   → builds earnings_valuation_data.parquet
  Step 2: Run train_earnings_model.py       → XGBoost validation of factor importances
  Step 3: Run test_valuation_hypothesis.py  → this script (statistical hypothesis test)

  Interpret results:
    • If Q4 (Strong growth) + 'Cheap' P/E bucket shows the highest median 3/5yr return
      AND the Mann-Whitney test is significant → hypothesis CONFIRMED.
    • If growth alone drives returns regardless of P/E → valuation entry point is less
      critical; focus on identifying the growth inflection early.
    • High Cohen's d (>0.5) means the effect is practically meaningful, not just
      statistically significant on a large sample.
""")


if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "..", "valuation_longterm_analysis.txt")
    out_path = os.path.normpath(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        sys.stdout = _Tee(f)
        run()
        sys.stdout = sys.stdout._stdout
    print(f"\nResults saved to: {out_path}")
