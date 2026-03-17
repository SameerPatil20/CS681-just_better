#!/usr/bin/env python3
"""
ci_3_4_validate.py

Usage:
    python3 ci_3_4_validate.py <runs_dir> <N> [-c CONF] [-s SEED] [--split sequential|random]

Example:
    python3 ci_3_4_validate.py runs 15 -c 95 -s 0
    python3 ci_3_4_validate.py runs 20 --split sequential

Notes:
- By default uses a random but reproducible split (seed 0). Use --split sequential to use runs
  1..floor(3N/4) as training and the rest as validation.
"""
import os
import re
import sys
import math
import argparse
from collections import defaultdict, OrderedDict

import numpy as np
import matplotlib.pyplot as plt

# Try scipy for exact t critical values
try:
    from scipy.stats import t as scipy_t
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False

# --- CONFIG / METRICS ---
METRICS = ['ResponseTime', 'Throughput', 'Goodput', 'Badput', 'Timeouts', 'Util']

ENTRY_RE = re.compile(r'###\s*ENTRY\s+users=(\d+)\s+run=(\d+)\s+seed=(\d+)\s*###', re.IGNORECASE)
END_RE = re.compile(r'###\s*END_ENTRY', re.IGNORECASE)
METRIC_RE = re.compile(
    r'ResponseTime=([\d\.]+).*?Throughput=([\d\.]+).*?goodput=([\d\.]+).*?badput=([\d\.]+).*?timedout=(\d+).*?Util=([\d\.]+)',
    re.IGNORECASE
)

# --- NUMERICAL UTILITIES (inverse normal / t-critical) ---
# Acklam approximation for inverse normal CDF (robust)
def inverse_normal_cdf(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p must be in (0,1)")
    a = [ -3.969683028665376e+01,  2.209460984245205e+02,
          -2.759285104469687e+02,  1.383577518672690e+02,
          -3.066479806614716e+01,  2.506628277459239e+00 ]
    b = [ -5.447609879822406e+01,  1.615858368580409e+02,
          -1.556989798598866e+02,  6.680131188771972e+01,
          -1.328068155288572e+01 ]
    c = [ -7.784894002430293e-03, -3.223964580411365e-01,
          -2.400758277161838e+00, -2.549732539343734e+00,
           4.374664141464968e+00,  2.938163982698783e+00 ]
    d = [ 7.784695709041462e-03,  3.224671290700398e-01,
          2.445134137142996e+00,  3.754408661907416e+00 ]
    plow = 0.02425
    phigh = 1 - plow
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        num = (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5])
        den = ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1.0)
        x = num / den
        return -x
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        num = (((((c[0]*q + c[1])*q + c[2])*q + c[3])*q + c[4])*q + c[5])
        den = ((((d[0]*q + d[1])*q + d[2])*q + d[3])*q + 1.0)
        x = num / den
        return x
    q = p - 0.5
    r = q * q
    num = (((((a[0]*r + a[1])*r + a[2])*r + a[3])*r + a[4])*r + a[5]) * q
    den = (((((b[0]*r + b[1])*r + b[2])*r + b[3])*r + b[4])*r + 1.0)
    return num / den

def approximate_t_from_z(z, df):
    if df <= 0:
        return z
    return z + (z**3 + z) / (4.0 * df)

def t_critical(confidence_percent: float, df: int) -> float:
    """
    two-sided t critical (upper quantile). confidence_percent like 95.0
    """
    alpha = 1.0 - (confidence_percent / 100.0)
    tail_prob = 1.0 - alpha / 2.0
    if df <= 0:
        return inverse_normal_cdf(tail_prob)
    if SCIPY_AVAILABLE:
        return float(scipy_t.ppf(tail_prob, df))
    z = inverse_normal_cdf(tail_prob)
    return approximate_t_from_z(z, df)

# --- PARSING RUN FILES ---
def parse_run_file(filepath):
    entries = []
    with open(filepath, 'r', errors='ignore') as f:
        content = f.read()
    for entry in ENTRY_RE.finditer(content):
        users = int(entry.group(1))
        run = int(entry.group(2))
        start = entry.end()
        end_match = END_RE.search(content, start)
        end = end_match.start() if end_match else len(content)
        block = content[start:end]
        m = METRIC_RE.search(block)
        if m:
            metrics = {
                'ResponseTime': float(m.group(1)),
                'Throughput': float(m.group(2)),
                'Goodput': float(m.group(3)),
                'Badput': float(m.group(4)),
                'Timeouts': float(int(m.group(5))),
                'Util': float(m.group(6))
            }
            entries.append((users, run, metrics))
    return entries

def collect_all_runs(runs_dir):
    agg = defaultdict(dict)  # users -> { run: metrics }
    files = sorted([f for f in os.listdir(runs_dir) if f.endswith('.log')])
    for fname in files:
        path = os.path.join(runs_dir, fname)
        for users, run, metrics in parse_run_file(path):
            if run not in agg[users]:
                agg[users][run] = metrics
    return OrderedDict(sorted(agg.items()))

# --- CORE: build CI from training runs, validate on validation runs ---
def ci_train_validate(samples, training_runs, validation_runs, conf):
    """
    samples: OrderedDict(users -> {run:metrics})
    training_runs, validation_runs: lists of run numbers
    Returns:
      summary dicts and arrays for plotting.
    """
    # arrays for plotting (per metric)
    users_list = sorted(samples.keys())
    k = len(users_list)
    means = {m: [np.nan]*k for m in METRICS}
    los =   {m: [np.nan]*k for m in METRICS}
    his =   {m: [np.nan]*k for m in METRICS}

    # validation scatter points (list of (x_idx, y_val, run_number)) per metric
    val_points = {m: [] for m in METRICS}

    # counts for coverage
    in_ci = {m: 0 for m in METRICS}
    total_val = {m: 0 for m in METRICS}

    for i, users in enumerate(users_list):
        runs_dict = samples[users]
        # training values for each metric (use any training runs present)
        for m in METRICS:
            tvals = [float(runs_dict[r][m]) for r in training_runs if r in runs_dict]
            if len(tvals) == 0:
                continue
            arr = np.array(tvals, dtype=float)
            n = len(arr)
            df = max(1, n-1)
            mean = float(arr.mean())
            if n >= 2:
                sd = float(arr.std(ddof=1))
                se = sd / math.sqrt(n)
                margin = t_critical(conf, df) * se
            else:
                margin = 0.0
            lo = mean - margin
            hi = mean + margin
            means[m][i] = mean
            los[m][i] = lo
            his[m][i] = hi

            # validate on all validation runs for this user (if present)
            for rval in validation_runs:
                if rval in runs_dict:
                    val = float(runs_dict[rval][m])
                    val_points[m].append((i, val, rval))
                    # count only when CI exists (we have mean/lo/hi)
                    total_val[m] += 1
                    if lo <= val <= hi:
                        in_ci[m] += 1

    return {
        'users': users_list,
        'means': means,
        'los': los,
        'his': his,
        'val_points': val_points,
        'in_ci': in_ci,
        'total_val': total_val
    }

# --- PLOTTING ---
def plot_results(outdir, conf, training_runs, validation_runs, res):
    plots_dir = os.path.join(outdir, "plots", "ci_3_4_validation")
    os.makedirs(plots_dir, exist_ok=True)

    users = res['users']
    xs = np.array(users)

    for m in METRICS:
        plt.figure(figsize=(10,6))
        lo = np.array(res['los'][m], dtype=float)
        hi = np.array(res['his'][m], dtype=float)
        mean = np.array(res['means'][m], dtype=float)

        # fill CI only where not NaN
        mask = ~np.isnan(lo) & ~np.isnan(hi)
        if mask.any():
            plt.fill_between(xs[mask], lo[mask], hi[mask], color='C0', alpha=0.25, label=f"{len(training_runs)}-run CI")
            plt.plot(xs[mask], mean[mask], linewidth=1.25, label="training mean")

        # scatter validation points, color per validation run (small markers)
        valpts = res['val_points'][m]
        if valpts:
            runs_present = sorted(set(pt[2] for pt in valpts))
            cmap = plt.get_cmap('tab10')
            run_to_color = {r: cmap(i % 10) for i, r in enumerate(runs_present)}
            for (i_idx, y, rnum) in valpts:
                plt.scatter(xs[i_idx], y, s=20, color=run_to_color[rnum], marker='x', label=f"val run {rnum}" if f"val run {rnum}" not in plt.gca().get_legend_handles_labels()[1] else "")
        plt.xlabel("Number of Users")
        plt.ylabel(m)
        title_pct = "N/A"
        if res['total_val'][m] > 0:
            title_pct = f"{100.0*res['in_ci'][m]/res['total_val'][m]:.1f}%"
        plt.title(f"{m} — CI built from runs {training_runs} (conf={conf:.1f}%) — validation coverage: {title_pct}")
        plt.grid(True)
        plt.legend(loc='best', fontsize='small', ncol=2)
        plt.tight_layout()
        fname = f"{m.lower()}_ci_train_{'_'.join(map(str,training_runs))}_val_{'_'.join(map(str,validation_runs))}.png"
        outpath = os.path.join(plots_dir, fname)
        plt.savefig(outpath)
        plt.close()
        print(f"[plot saved] {outpath}")

    # write report text
    rpt_lines = []
    rpt_lines.append(f"CI coverage report (CI built from training runs = {training_runs}; validation runs = {validation_runs}; conf={conf}%)")
    for m in METRICS:
        tot = res['total_val'][m]
        inn = res['in_ci'][m]
        if tot:
            rpt_lines.append(f" {m}: {inn}/{tot} => {100.0*inn/tot:.1f}%")
        else:
            rpt_lines.append(f" {m}: no validation points (N/A)")
    rpt_text = "\n".join(rpt_lines)
    with open(os.path.join(plots_dir, "ci_coverage_report.txt"), "w") as rf:
        rf.write(rpt_text + "\n")
    print("\n" + rpt_text)
    print(f"\nPlots + report saved in: {plots_dir}")

# --- MAIN CLI ---
def main():
    p = argparse.ArgumentParser(description="Build CI from 3/4 of runs and validate on remaining 1/4")
    p.add_argument("runs_dir", help="Directory containing .log files")
    p.add_argument("N", type=int, help="Total number of runs (numbered 1..N expected)")
    p.add_argument("-c", "--conf", type=float, default=95.0, help="Confidence percent (default 95)")
    p.add_argument("-s", "--seed", type=int, default=0, help="Random seed for split (default 0)")
    p.add_argument("--split", choices=['random', 'sequential'], default='random',
                   help="How to choose the 3/4 training runs: 'random' (default) or 'sequential' (1..floor(3N/4))")
    args = p.parse_args()

    runs_dir = args.runs_dir
    N = args.N
    conf = args.conf

    if N < 2:
        print("Need at least N>=2 runs.")
        sys.exit(1)

    if not os.path.isdir(runs_dir):
        print("Directory does not exist:", runs_dir)
        sys.exit(2)

    samples = collect_all_runs(runs_dir)
    if not samples:
        print("No samples found in directory:", runs_dir)
        sys.exit(3)

    # available run numbers in dataset (union across users)
    present_runs = set()
    for u, d in samples.items():
        present_runs.update(d.keys())
    expected_runs = list(range(1, N+1))
    missing = sorted(set(expected_runs) - present_runs)
    if missing:
        print("Warning: These expected run numbers (1..N) are not present in any logs:", missing)
        print("Script will continue but those runs will be ignored in splits if absent.\n")

    # decide split
    all_runs = [r for r in expected_runs if r in present_runs]
    if len(all_runs) < 2:
        print("Not enough runs present to split.")
        sys.exit(4)

    if args.split == 'sequential':
        k = max(1, math.floor(3 * len(all_runs) / 4))
        training_runs = all_runs[:k]
        validation_runs = all_runs[k:]
    else:
        # random split but reproducible with seed
        rng = np.random.default_rng(args.seed)
        shuffled = list(all_runs)
        rng.shuffle(shuffled)
        k = max(1, math.floor(3 * len(shuffled) / 4))
        training_runs = sorted(shuffled[:k])
        validation_runs = sorted(shuffled[k:])

    if len(training_runs) == 0 or len(validation_runs) == 0:
        print("Split produced empty training or validation set. Try different N or split mode.")
        sys.exit(5)

    print(f"Training runs ({len(training_runs)}): {training_runs}")
    print(f"Validation runs ({len(validation_runs)}): {validation_runs}")
    if not SCIPY_AVAILABLE:
        print("scipy not found: using normal+Cornish–Fisher approx for t-critical. Install scipy for exact values.")

    res = ci_train_validate(samples, training_runs, validation_runs, conf)
    plot_results(runs_dir, conf, training_runs, validation_runs, res)

if __name__ == "__main__":
    main()