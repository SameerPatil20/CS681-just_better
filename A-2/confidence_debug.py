#!/usr/bin/env python3
"""
plot_selected_runs.py

Usage:
    python3 plot_selected_runs.py <runs_dir> <n> <run1> <run2> ... <runn>

Example:
    python3 plot_selected_runs.py runs 4 1 2 3 15

Produces one PNG per metric in: <runs_dir>/plots/selected_runs/
"""

import os
import sys
import re
import argparse
from collections import defaultdict, OrderedDict

import numpy as np
import matplotlib.pyplot as plt

# --- CONFIG ---
METRICS = ['ResponseTime', 'Throughput', 'Goodput', 'Badput', 'Timeouts', 'Util']

# regex patterns (matches your log ENTRY format)
ENTRY_RE = re.compile(r'###\s*ENTRY\s+users=(\d+)\s+run=(\d+)\s+seed=(\d+)\s*###', re.IGNORECASE)
END_RE = re.compile(r'###\s*END_ENTRY', re.IGNORECASE)
METRIC_RE = re.compile(
    r'ResponseTime=([\d\.]+).*?Throughput=([\d\.]+).*?goodput=([\d\.]+).*?badput=([\d\.]+).*?timedout=(\d+).*?Util=([\d\.]+)',
    re.IGNORECASE
)

# --- parsing helpers ---

def parse_run_file(filepath):
    """
    Parse a single log file and return list of (users:int, run:int, metrics:dict).
    """
    entries = []
    with open(filepath, "r", errors="ignore") as f:
        content = f.read()

    for ent in ENTRY_RE.finditer(content):
        users = int(ent.group(1))
        run = int(ent.group(2))

        start = ent.end()
        end_match = END_RE.search(content, start)
        end = end_match.start() if end_match else len(content)
        block = content[start:end]

        m = METRIC_RE.search(block)
        if not m:
            continue

        metrics = {
            'ResponseTime': float(m.group(1)),
            'Throughput': float(m.group(2)),
            'Goodput': float(m.group(3)),
            'Badput': float(m.group(4)),
            'Timeouts': float(int(m.group(5))),  # keep numeric but as float for plotting
            'Util': float(m.group(6))
        }
        entries.append((users, run, metrics))
    return entries

def collect_all_runs(runs_dir):
    """
    Return OrderedDict(users -> dict(run -> metrics))
    """
    agg = defaultdict(dict)
    files = sorted([f for f in os.listdir(runs_dir) if f.endswith('.log')])
    for fname in files:
        path = os.path.join(runs_dir, fname)
        for users, run, metrics in parse_run_file(path):
            # keep first-seen entry for (users, run)
            if run not in agg[users]:
                agg[users][run] = metrics
    return OrderedDict(sorted(agg.items()))

# --- plotting ---

def plot_runs_overlay(samples, selected_runs, outdir, metrics_to_plot=None):
    """
    samples: OrderedDict(users -> {run: metrics})
    selected_runs: list of ints
    """
    if metrics_to_plot is None:
        metrics_to_plot = METRICS

    plots_dir = os.path.join(outdir, "plots", "selected_runs")
    os.makedirs(plots_dir, exist_ok=True)

    # union of users across all runs (sorted)
    all_users = sorted(samples.keys())

    # For nicer x-axis when user values are not dense, keep them as ints
    xs = np.array(all_users)

    # For each metric, create one figure that overlays all selected runs
    for metric in metrics_to_plot:
        plt.figure(figsize=(10, 6))
        missing_per_run = {}
        for run in selected_runs:
            # build y aligned to xs; put np.nan where value missing
            ys = []
            missing = 0
            for users in all_users:
                m = samples.get(users, {})
                if run in m:
                    ys.append(float(m[run].get(metric, np.nan)))
                else:
                    ys.append(np.nan)
                    missing += 1
            missing_per_run[run] = missing
            ys = np.array(ys, dtype=float)

            # plot; matplotlib will break lines at NaNs
            plt.plot(xs, ys, linewidth=1.25, markersize=3, label=f"run {run}")

        plt.xlabel("Number of Users")
        plt.ylabel(metric)
        plt.title(f"{metric} — overlay runs: {', '.join(map(str, selected_runs))}")
        plt.grid(True)
        plt.legend(loc='best', fontsize='small')
        plt.tight_layout()

        outpath = os.path.join(plots_dir, f"{metric.lower()}_overlay_runs_{'_'.join(map(str, selected_runs))}.png")
        plt.savefig(outpath)
        plt.close()

        # print a small summary about missing data for this metric
        miss_summary = ", ".join([f"run {r}: missing {missing_per_run[r]}/{len(all_users)}" for r in selected_runs])
        print(f"[{metric}] saved -> {outpath}; missing: {miss_summary}")

    print(f"\nAll plots saved in: {plots_dir}")

# --- CLI ---

def main():
    p = argparse.ArgumentParser(description="Plot selected runs overlaid for each metric.")
    p.add_argument("runs_dir", help="Directory containing .log run files")
    p.add_argument("n", type=int, help="Number of run indices to plot (must match count of following args)")
    p.add_argument("runs", type=int, nargs='+', help="Run numbers to plot (space separated)")
    p.add_argument("--metrics", nargs='+', help="Optional subset of metrics to plot (default: all)")
    args = p.parse_args()

    if args.n <= 0:
        print("n must be >= 1")
        sys.exit(1)

    if len(args.runs) != args.n:
        print(f"Expected {args.n} run numbers but got {len(args.runs)}.")
        print("Usage example: python3 plot_selected_runs.py runs 4 1 2 3 15")
        sys.exit(2)

    if not os.path.isdir(args.runs_dir):
        print("Directory does not exist:", args.runs_dir)
        sys.exit(3)

    samples = collect_all_runs(args.runs_dir)
    if not samples:
        print("No samples found in directory:", args.runs_dir)
        sys.exit(4)

    # check whether the provided run numbers appear at all in the dataset
    provided = set(args.runs)
    present_runs = set()
    for users_map in samples.values():
        present_runs.update(users_map.keys())
    missing_runs = sorted(list(provided - present_runs))
    if missing_runs:
        print("Warning: the following requested run numbers do not appear in any log entries:", missing_runs)
        print("The script will still run but those runs will be empty on the plots.\n")

    plot_runs_overlay(samples, args.runs, args.runs_dir, metrics_to_plot=args.metrics)

if __name__ == "__main__":
    main()