import os
import re
import math
import argparse
from collections import defaultdict, OrderedDict

import numpy as np
import matplotlib.pyplot as plt

# Metrics to track
METRICS = ['ResponseTime', 'Throughput', 'Goodput', 'Badput', 'Timeouts', 'Util']

ENTRY_RE = re.compile(
    r'###\s*ENTRY\s+users=(\d+)\s+run=(\d+)\s+seed=(\d+)\s*###',
    re.IGNORECASE
)
END_RE = re.compile(r'###\s*END_ENTRY', re.IGNORECASE)

KV_RE = re.compile(r'(\w+)=([\d\.]+)', re.IGNORECASE)

# ---- t critical ----
try:
    from scipy.stats import t
    def t_critical(conf, df):
        return float(t.ppf(1 - (1 - conf / 100) / 2, df))
except Exception:
    def t_critical(conf, df):
        return 1.96


# ---- parsing ----
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

        kv_pairs = dict((k.lower(), float(v)) for k, v in KV_RE.findall(block))

        try:
            metrics = {
                'ResponseTime': kv_pairs['responsetime'],
                'Throughput': kv_pairs['throughput'],
                'Goodput': kv_pairs.get('goodput', 0.0),
                'Badput': kv_pairs.get('badput', 0.0),
                'Timeouts': kv_pairs.get('timedout', 0.0),
                'Util': kv_pairs.get('util', 0.0),
            }
        except KeyError:
            continue

        entries.append((users, run, metrics))

    return entries


# ---- aggregation ----
def collect_all_runs(runs_dir):
    agg = defaultdict(dict)

    for fname in sorted(os.listdir(runs_dir)):
        if not fname.endswith(".log"):
            continue

        fpath = os.path.join(runs_dir, fname)

        for users, run, metrics in parse_run_file(fpath):
            agg[users][run] = metrics  # overwrite safely

    return OrderedDict(sorted(agg.items()))


# ---- stats ----
def compute_ci_and_mean(samples, conf):
    users_list = sorted(samples.keys())
    results = {m: {"mean": [], "lo": [], "hi": []} for m in METRICS}

    for users in users_list:
        runs = samples[users]

        # print(f"Users={users}, Runs collected={len(runs)}")

        for m in METRICS:
            vals = [runs[r][m] for r in sorted(runs.keys())]

            if len(vals) < 2:
                results[m]["mean"].append(np.nan)
                results[m]["lo"].append(np.nan)
                results[m]["hi"].append(np.nan)
                continue

            arr = np.array(vals, dtype=float)
            n = len(arr)

            mean = arr.mean()
            sd = arr.std(ddof=1)

            tcrit = t_critical(conf, n - 1)
            margin = tcrit * (sd / math.sqrt(n))

            results[m]["mean"].append(mean)
            results[m]["lo"].append(mean - margin)
            results[m]["hi"].append(mean + margin)

    return users_list, results


# ---- plotting ----
def plot_all(users, results, outdir):
    plots_dir = os.path.join(outdir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    xs = np.array(users)

    # Individual plots
    for m in METRICS:
        plt.figure(figsize=(10, 6))

        lo = np.array(results[m]["lo"])
        hi = np.array(results[m]["hi"])
        mean = np.array(results[m]["mean"])
        mask = ~np.isnan(lo)

        # --- CI as vertical lines ---
        plt.vlines(xs[mask], lo[mask], hi[mask], alpha=1, label="CI", color="red")

        # --- Mean line ---
        plt.plot(xs[mask], mean[mask], linewidth=1.5, label="Mean")

        plt.xlabel("Number of Users")
        plt.ylabel(m)
        plt.title(f"{m} (Mean ± CI)")
        plt.grid()
        plt.legend()

        plt.savefig(os.path.join(plots_dir, f"{m}.png"), dpi=300, bbox_inches='tight')
        plt.close()

    # Combined plot
    plt.figure(figsize=(10, 6))

    for m in ['Throughput', 'Goodput', 'Badput']:
        lo = np.array(results[m]["lo"])
        hi = np.array(results[m]["hi"])
        mean = np.array(results[m]["mean"])
        mask = ~np.isnan(lo)

        plt.vlines(xs[mask], lo[mask], hi[mask], alpha=1, color = "red")
        plt.plot(xs[mask], mean[mask], label=m, linewidth=1.5)

    plt.xlabel("Number of Users")
    plt.ylabel("Requests/sec")
    plt.title("Throughput / Goodput / Badput (Mean ± CI)")
    plt.grid()
    plt.legend()

    plt.savefig(os.path.join(plots_dir, "throughput_goodput_badput.png"), dpi=300, bbox_inches='tight')
    plt.close()

    print("\nPlots saved to:", plots_dir)


# ---- main ----
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_dir", help="Directory containing log files")
    parser.add_argument("-c", "--conf", type=float, default=95.0)

    args = parser.parse_args()

    samples = collect_all_runs(args.runs_dir)
    users, results = compute_ci_and_mean(samples, args.conf)
    plot_all(users, results, args.runs_dir)


if __name__ == "__main__":
    main()