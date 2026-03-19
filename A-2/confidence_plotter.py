import os
import re
import sys
import math
import argparse
from collections import defaultdict, OrderedDict

import numpy as np
import matplotlib.pyplot as plt

METRICS = ['ResponseTime', 'Throughput', 'Goodput', 'Badput', 'Timeouts', 'Util']

ENTRY_RE = re.compile(
    r'###\s*ENTRY\s+users=(\d+)\s+run=(\d+)\s+seed=(\d+)\s*###',
    re.IGNORECASE
)
END_RE = re.compile(r'###\s*END_ENTRY', re.IGNORECASE)
METRIC_RE = re.compile(
    r'ResponseTime=([\d\.]+).*?Throughput=([\d\.]+).*?goodput=([\d\.]+).*?badput=([\d\.]+).*?timedout=(\d+).*?Util=([\d\.]+)',
    re.IGNORECASE
)

try:
    from scipy.stats import t

    def t_critical(conf, df):
        return float(t.ppf(1 - (1 - conf / 100) / 2, df))
except Exception:
    def t_critical(conf, df):
        return 1.96


def parse_run_file(filepath):
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
            'Timeouts': float(int(m.group(5))),
            'Util': float(m.group(6))
        }
        entries.append((users, run, metrics))

    return entries


def collect_all_runs(runs_dir):
    agg = defaultdict(dict)

    for fname in sorted(os.listdir(runs_dir)):
        if not fname.endswith(".log"):
            continue

        fpath = os.path.join(runs_dir, fname)
        for users, run, metrics in parse_run_file(fpath):
            if run not in agg[users]:
                agg[users][run] = metrics

    return OrderedDict(sorted(agg.items()))


def compute_ci_and_valmean(samples, N, conf):
    users_list = sorted(samples.keys())
    k = int(0.75 * N)
    train_runs = list(range(1, k + 1))
    val_runs = list(range(k + 1, N + 1))

    print("Train runs:", train_runs)
    print("Val runs:", val_runs)

    results = {m: {"mean": [], "lo": [], "hi": [], "val_mean": []} for m in METRICS}

    for users in users_list:
        runs = samples[users]

        for m in METRICS:
            train_vals = [runs[r][m] for r in train_runs if r in runs]
            val_vals = [runs[r][m] for r in val_runs if r in runs]

            if len(train_vals) < 2 or len(val_vals) == 0:
                results[m]["mean"].append(np.nan)
                results[m]["lo"].append(np.nan)
                results[m]["hi"].append(np.nan)
                results[m]["val_mean"].append(np.nan)
                continue

            train_arr = np.array(train_vals)
            val_arr = np.array(val_vals)

            n = len(train_arr)
            mean = train_arr.mean()
            sd = train_arr.std(ddof=1)
            tcrit = t_critical(conf, n - 1)
            margin = tcrit * (sd / math.sqrt(n))

            lo = mean - margin
            hi = mean + margin

            results[m]["mean"].append(mean)
            results[m]["lo"].append(lo)
            results[m]["hi"].append(hi)
            results[m]["val_mean"].append(val_arr.mean())

    return users_list, results


def plot_all(users, results, outdir):
    plots_dir = os.path.join(outdir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    xs = np.array(users)

    for m in METRICS:
        plt.figure(figsize=(10, 6))
        lo = np.array(results[m]["lo"])
        hi = np.array(results[m]["hi"])
        val_mean = np.array(results[m]["val_mean"])
        mask = ~np.isnan(lo)

        # CI as vertical lines
        plt.vlines(xs[mask], lo[mask], hi[mask], color="green", alpha=0.8, label="CI (train)")
        plt.plot(xs[mask], val_mean[mask], linestyle='-', label="Mean", color="red", linewidth=0.8)

        plt.xlabel("Users")
        plt.ylabel(m)
        plt.title(f"{m}: Mean with CI")
        plt.grid()
        plt.legend()
        plt.savefig(os.path.join(plots_dir, f"{m}.png"))
        plt.close()

    plt.figure(figsize=(10, 6))

    ci_colors = {
        'Throughput': 'blue',
        'Goodput': 'green',
        'Badput': 'red'
    }
    val_colors = {
        'Throughput': 'navy',
        'Goodput': 'darkgreen',
        'Badput': 'darkred'
    }

    for m in ['Throughput', 'Goodput', 'Badput']:
        lo = np.array(results[m]["lo"])
        hi = np.array(results[m]["hi"])
        val_mean = np.array(results[m]["val_mean"])
        mask = ~np.isnan(lo)

        plt.vlines(xs[mask], lo[mask], hi[mask], color=ci_colors[m], alpha=0.6, label=f"{m} CI")
        plt.plot(xs[mask], val_mean[mask], linestyle='-', color=val_colors[m], label=f"{m} (mean)", linewidth=0.8)

    plt.xlabel("Users")
    plt.ylabel("Requests/sec")
    plt.title("Throughput / Goodput / Badput (CI + Mean)")
    plt.grid()
    plt.legend()
    plt.savefig(os.path.join(plots_dir, "throughput_goodput_badput.png"))
    plt.close()

    print("\nPlots saved to:", plots_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_dir")
    parser.add_argument("-n", "--runs", type=int, required=True)
    parser.add_argument("-c", "--conf", type=float, default=95.0)
    args = parser.parse_args()

    samples = collect_all_runs(args.runs_dir)
    users, results = compute_ci_and_valmean(samples, args.runs, args.conf)
    plot_all(users, results, args.runs_dir)


if __name__ == "__main__":
    main()