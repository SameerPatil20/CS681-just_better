import os
import re
import sys
import math
import argparse
from collections import defaultdict, OrderedDict
import numpy as np
import matplotlib.pyplot as plt

METRICS = ['ResponseTime', 'Throughput', 'Goodput', 'Badput', 'Timeouts', 'Util']
ENTRY_RE = re.compile(r'###\s*ENTRY\s+users=(\d+)\s+run=(\d+)\s+seed=(\d+)\s*###', re.IGNORECASE)
END_RE = re.compile(r'###\s*END_ENTRY', re.IGNORECASE)
METRIC_RE = re.compile(
    r'ResponseTime=([\d\.]+).*?Throughput=([\d\.]+).*?goodput=([\d\.]+).*?badput=([\d\.]+).*?timedout=(\d+).*?Util=([\d\.]+)',
    re.IGNORECASE
)

try:
    from scipy.stats import t
    def t_critical(conf, df):
        return float(t.ppf(1 - (1-conf/100)/2, df))
except:
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

        for users, run, metrics in parse_run_file(os.path.join(runs_dir, fname)):
            if run not in agg[users]:
                agg[users][run] = metrics

    return OrderedDict(sorted(agg.items()))

def validate_mean_ci(samples, runs_dir, total_runs, conf):
    plots_dir = os.path.join(runs_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)

    all_runs = list(range(1, total_runs + 1))
    k = int(0.75 * len(all_runs))

    train_runs = all_runs[:k]
    val_runs = all_runs[k:]

    print("Train runs:", train_runs)
    print("Val runs:", val_runs)

    users_list = sorted(samples.keys())

    for metric in METRICS:
        xs = []
        inside_flags = []

        print(f"\n==== {metric} ====")

        for users in users_list:
            runs = samples[users]
            train_vals = [runs[r][metric] for r in train_runs if r in runs]
            val_vals   = [runs[r][metric] for r in val_runs if r in runs]
            if len(train_vals) < 2 or len(val_vals) == 0:
                continue
            train_arr = np.array(train_vals)
            val_arr   = np.array(val_vals)
            n = len(train_arr)
            mean = train_arr.mean()
            sd = train_arr.std(ddof=1)
            tcrit = t_critical(conf, n-1)
            n_train = len(train_arr)
            n_val = len(val_arr)
            margin = tcrit * sd * math.sqrt(1/n_train + 1/n_val)
            lo = mean - margin
            hi = mean + margin
            val_mean = val_arr.mean()
            inside = (lo <= val_mean <= hi)
            xs.append(users)
            inside_flags.append(1 if inside else 0)
            # print(f"users={users:4d} | val_mean={val_mean:.3f} | CI=[{lo:.3f}, {hi:.3f}] | {'IN' if inside else 'OUT'}")
        total = len(inside_flags)
        success = sum(inside_flags)
        if total > 0:
            print(f"\nCoverage: {success}/{total} = {100*success/total:.2f}%")

        # plot
        # plt.figure(figsize=(8,5))
        # plt.plot(xs, inside_flags, marker='o')
        # plt.axhline(1.0, linestyle='--', label='Ideal (inside)')

        # plt.xlabel("Users")
        # plt.ylabel("Inside CI (1=yes, 0=no)")
        # plt.title(f"{metric} — Validation Mean inside CI")
        # plt.grid(True)
        # plt.legend()

        # outpath = os.path.join(plots_dir, f"{metric}_mean_validation.png")
        # plt.savefig(outpath)
        # plt.close()

        # print(f"Plot saved: {outpath}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_dir", help="Directory with log files")
    parser.add_argument("-n", "--runs", type=int, required=True, help="Total number of runs")
    parser.add_argument("-c", "--conf", type=float, default=95.0, help="Confidence level")
    args = parser.parse_args()
    if not os.path.isdir(args.runs_dir):
        print("Directory does not exist:", args.runs_dir)
        sys.exit(1)
    samples = collect_all_runs(args.runs_dir)
    if not samples:
        print("No data found")
        sys.exit(2)
    validate_mean_ci(samples, args.runs_dir, args.runs, args.conf)


if __name__ == "__main__":
    main()