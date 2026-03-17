#!/usr/bin/env python3
"""
parse_and_plot_ci.py

Usage:
    python3 parse_and_plot_ci.py <runs_dir> [-c CONF]
Example:
    python3 parse_and_plot_ci.py runs -c 97   # 97% confidence intervals (default)
    python3 parse_and_plot_ci.py runs -c 90   # 90% CI

Behavior:
- Reads .log files in <runs_dir> (expected entries like ### ENTRY users=... ### ... ### END_ENTRY).
- Pools samples per users across run files (e.g., 15 runs).
- Computes mean and two-sided CI at the requested confidence level using Student-t critical values (exact if scipy available).
- If scipy is not present, uses a normal quantile and a Cornish–Fisher first-order correction to approximate t-critical.
- Plots Run 1 (no markers) and a blue shaded CI band for each metric.
"""

import os
import re
import math
import sys
import argparse
from collections import defaultdict, OrderedDict

import numpy as np
import matplotlib.pyplot as plt

# Try to import scipy for exact t-critical; fall back if not available
try:
    from scipy.stats import t as scipy_t
    SCIPY_AVAILABLE = True
except Exception:
    SCIPY_AVAILABLE = False

# --- CONFIG / METRICS ---
METRICS = ['ResponseTime', 'Throughput', 'Goodput', 'Badput', 'Timeouts', 'Util']

# regex patterns
ENTRY_RE = re.compile(r'###\s*ENTRY\s+users=(\d+)\s+run=(\d+)\s+seed=(\d+)\s*###', re.IGNORECASE)
END_RE = re.compile(r'###\s*END_ENTRY', re.IGNORECASE)
METRIC_RE = re.compile(
    r'ResponseTime=([\d\.]+).*?Throughput=([\d\.]+).*?goodput=([\d\.]+).*?badput=([\d\.]+).*?timedout=(\d+).*?Util=([\d\.]+)',
    re.IGNORECASE
)

# --- NUMERICAL UTILITIES ---

# Acklam / Beasley-Springer-Moro inverse normal CDF approximation (probit).
# Reliable across a wide range of probabilities.
def inverse_normal_cdf(p):
    if p <= 0.0 or p >= 1.0:
        raise ValueError("p must be in (0,1)")
    # Coefficients for approximation
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

    # Define break-points.
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

def approximate_t_critical_from_z(z, df):
    """
    Cornish–Fisher first-order correction approx:
    t_crit ≈ z + (z^3 + z) / (4*df)
    (works reasonably for df >= ~5; for larger df it approaches z)
    """
    if df <= 0:
        return z
    return z + (z**3 + z) / (4.0 * df)

def t_critical(confidence_percent, df):
    """
    Returns two-sided t-critical value for the requested confidence percentage and df.
    If scipy is available, uses exact t.ppf.
    Otherwise falls back to normal quantile + Cornish-Fisher correction.
    """
    alpha = 1.0 - (confidence_percent / 100.0)
    tail_prob = 1.0 - alpha / 2.0  # upper quantile

    if df <= 0:
        # degenerate: fallback to normal
        z = inverse_normal_cdf(tail_prob)
        return z

    if SCIPY_AVAILABLE:
        # exact
        return float(scipy_t.ppf(tail_prob, df))
    else:
        # approximate
        z = inverse_normal_cdf(tail_prob)
        t_approx = approximate_t_critical_from_z(z, df)
        return t_approx

# --- PARSING RUN FILES ---

def parse_run_file(filepath):
    """
    Parse a single run file containing ENTRY blocks.
    Return dict: users -> list of metrics (for that file)
    """
    per_user = defaultdict(list)
    with open(filepath, 'r', errors='ignore') as f:
        content = f.read()

    for entry in ENTRY_RE.finditer(content):
        users = int(entry.group(1))
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
                'Timeouts': int(m.group(5)),
                'Util': float(m.group(6))
            }
            per_user[users].append(metrics)
    return per_user

def collect_all_runs(runs_dir):
    """
    Collects and aggregates metrics across all .log files found in runs_dir.
    Returns OrderedDict(users -> list of metric dicts pooled across all runs).
    """
    files = sorted([f for f in os.listdir(runs_dir) if f.endswith('.log')])
    if not files:
        return OrderedDict()

    aggregate = defaultdict(list)
    for fname in files:
        path = os.path.join(runs_dir, fname)
        per_user = parse_run_file(path)
        for users, vals in per_user.items():
            for v in vals:
                aggregate[users].append(v)
    return OrderedDict(sorted(aggregate.items()))

# --- PLOTTING / COMPUTATION ---

def compute_and_plot(samples, outdir, confidence_percent):
    """
    samples: OrderedDict(users -> list of metric dicts)
    confidence_percent: e.g., 97.0
    """
    os.makedirs(os.path.join(outdir, "plots"), exist_ok=True)

    xs = []
    means = {m: [] for m in METRICS}
    los = {m: [] for m in METRICS}
    his = {m: [] for m in METRICS}
    run1_vals = {m: [] for m in METRICS}

    for users, runs in samples.items():
        n = len(runs)
        if n == 0:
            continue
        xs.append(users)
        df = max(1, n - 1)  # degrees of freedom
        tcrit = t_critical(confidence_percent, df)

        for m in METRICS:
            arr = np.array([r[m] for r in runs], dtype=float)
            mean = float(arr.mean())
            if n >= 2:
                sd = float(arr.std(ddof=1))
                se = sd / math.sqrt(n)
                margin = tcrit * se
            else:
                margin = 0.0
            lo = mean - margin
            hi = mean + margin

            means[m].append(mean)
            los[m].append(lo)
            his[m].append(hi)

            # run 1 sample (assumes file ordering includes run_1.log first)
            run1_vals[m].append(float(arr[5]))

    # Sort xs (they should already be sorted), convert to numpy arrays for plotting
    xs = np.array(xs)

    # Individual metric plots
    for m in METRICS:
        plt.figure(figsize=(9, 5))
        # CI band (blue)
        plt.fill_between(xs, los[m], his[m], color='yellow', alpha=0.6)
        # Run 1 line (no markers)
        plt.plot(xs, run1_vals[m], linewidth=1)
        plt.xlabel("Number of Users")
        plt.ylabel(m)
        plt.title(f"{m} vs Users (Run 1 + {confidence_percent:.1f}% CI)")
        plt.grid(True)
        plt.tight_layout()
        outpath = os.path.join(outdir, "plots", f"{m.lower()}_ci.png")
        plt.savefig(outpath)
        plt.close()

    # Combined throughput/goodput/badput
    plt.figure(figsize=(10, 6))
    for m in ['Throughput', 'Goodput', 'Badput']:
        plt.fill_between(xs, los[m], his[m], color='yellow', alpha=0.6)
        plt.plot(xs, run1_vals[m], linewidth=1, label=m)
    plt.xlabel("Number of Users")
    plt.ylabel("Requests/sec")
    plt.title(f"Throughput / Goodput / Badput (Run 1 + {confidence_percent:.1f}% CI)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    outpath = os.path.join(outdir, "plots", "throughput_goodput_badput_ci.png")
    plt.savefig(outpath)
    plt.close()

# --- CLI / ENTRYPOINT ---

def main():
    parser = argparse.ArgumentParser(description="Parse run logs and plot run1 + CI band.")
    parser.add_argument("runs_dir", help="Directory containing run_1.log ... run_15.log (or other .log files)")
    parser.add_argument("-c", "--conf", type=float, default=97.0,
                        help="Confidence percentage for two-sided CI (default: 97.0). Eg: 90, 95, 97, 99")
    args = parser.parse_args()

    runs_dir = args.runs_dir
    conf = args.conf
    if conf <= 0 or conf >= 100:
        print("Confidence percentage must be between 0 and 100 (exclusive).")
        sys.exit(2)

    if not os.path.isdir(runs_dir):
        print("Directory does not exist:", runs_dir)
        sys.exit(3)

    samples = collect_all_runs(runs_dir)
    if not samples:
        print("No samples found in directory:", runs_dir)
        sys.exit(4)

    if SCIPY_AVAILABLE:
        print("scipy detected: using exact Student-t quantiles for CI.")
    else:
        print("scipy not detected: using normal quantile + Cornish–Fisher approx for Student-t critical values.")
        print("This approximation is good for df >= ~5; for small dfs consider installing scipy for exact values.")
        print("Install with: pip install scipy")

    print(f"Computing {conf:.1f}% two-sided CI (pooled n varies per users).")
    compute_and_plot(samples, runs_dir, conf)
    print("Done. Plots saved at:", os.path.join(runs_dir, "plots"))

if __name__ == "__main__":
    main()