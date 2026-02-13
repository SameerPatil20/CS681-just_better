import re
import argparse
from pathlib import Path
import sys
import pandas as pd
import matplotlib.pyplot as plt
import math

LOG_LINE_PATTERN = re.compile(r'(\w+)=([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)')
DEFAULT_METRICS = ['Throughput', 'AvgLatency', 'ResponseTime', 'Failures', 'Successes','CPU']


def parse_log(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {path}")

    rows = []
    with path.open('r', encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            d = {}
            for m in LOG_LINE_PATTERN.finditer(ln):
                key = m.group(1)
                val = m.group(2)
                if re.fullmatch(r'[+-]?\d+', val):
                    v = int(val)
                else:
                    v = float(val)
                d[key] = v
            if d:
                rows.append(d)
    if not rows:
        raise ValueError(f"No parseable rows found in {path}")

    df = pd.DataFrame(rows)
    if 'N' in df.columns:
        df = df.sort_values('N').reset_index(drop=True)
    return df


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def plot_metrics(df: pd.DataFrame, metrics, outdir: Path, show=False, source_desc=None):
    saved = []
    for metric in metrics:
        if metric not in df.columns:
            print(f"Skipping {metric}: not present in parsed data")
            continue
        plt.figure(figsize=(8,5))
        plt.plot(df['N'], df[metric], marker='o')
        plt.xlabel('N (clients)')
        plt.ylabel(metric)
        title = f"{metric} vs N"
        if source_desc:
            title += f" ({source_desc})"
        plt.title(title)
        plt.grid(True)
        fname = outdir / f'plot_{metric}.png'
        plt.savefig(fname, bbox_inches='tight')
        saved.append(fname)
        if show:
            plt.show()
        plt.close()
    return saved


def plot_response_vs_throughput(df: pd.DataFrame, outdir: Path, show=False, source_desc=None):
    if 'Throughput' not in df.columns or 'ResponseTime' not in df.columns:
        print("Skipping ResponseTime vs Throughput: required columns not present")
        return None

    sub = df[['Throughput', 'ResponseTime']].dropna()
    if sub.empty:
        print("Skipping ResponseTime vs Throughput: no valid data points")
        return None

    plt.figure(figsize=(8, 5))
    plt.plot(sub['Throughput'], sub['ResponseTime'], marker='o', linestyle='-')
    plt.xlabel('Throughput (req/s)')
    plt.ylabel('ResponseTime (s)')
    title = "ResponseTime vs Throughput"
    if source_desc:
        title += f" ({source_desc})"
    plt.title(title)
    plt.grid(True)

    fname = outdir / 'plot_ResponseTime_vs_Throughput.png'
    plt.savefig(fname, bbox_inches='tight')

    if show:
        plt.show()
    plt.close()

    print(f"Saved {fname}")
    return fname


def plot_response_vs_throughput(df: pd.DataFrame, outdir: Path, show=False, source_desc=None):
    if 'Throughput' not in df.columns or 'CPU' not in df.columns:
        print("Skipping ResponseTime vs Throughput: required columns not present")
        return None

    sub = df[['Throughput', 'CPU']].dropna()
    if sub.empty:
        print("Skipping ResponseTime vs Throughput: no valid data points")
        return None

    plt.figure(figsize=(8, 5))
    plt.plot(sub['Throughput'], sub['CPU'], marker='o', linestyle='-')
    plt.xlabel('Throughput (req/s)')
    plt.ylabel('CPU (%)')
    title = "CPU vs Throughput"
    if source_desc:
        title += f" ({source_desc})"
    plt.title(title)
    plt.grid(True)

    fname = outdir / 'plot_CPU_vs_Throughput.png'
    plt.savefig(fname, bbox_inches='tight')

    if show:
        plt.show()
    plt.close()

    print(f"Saved {fname}")
    return fname


def plot_inferred_think_time(df: pd.DataFrame, outdir: Path, show=False, source_desc=None):

    if 'Throughput' not in df.columns or 'N' not in df.columns:
        print("Skipping inferred think time: required columns 'N' and 'Throughput' not present")
        return None

    if 'ResponseTime' not in df.columns and 'AvgLatency' in df.columns:
        print("Note: 'ResponseTime' column not found — using 'AvgLatency' as ResponseTime for inference")
        df = df.copy()
        df['ResponseTime'] = df['AvgLatency']

    if 'ResponseTime' not in df.columns:
        print("Skipping inferred think time: no ResponseTime or AvgLatency column available")
        return None

    sub = df[['N', 'Throughput', 'ResponseTime']].dropna()
    n_list = []
    think_list = []
    for row in sub.itertuples(index=False):
        N = float(row[0])
        tput = float(row[1])
        resp = float(row[2])
        if tput == 0:
            continue
        inferred = (N / tput) - resp
        n_list.append(N)
        think_list.append(inferred)

    if not n_list:
        print("Skipping inferred think time: no valid data points after filtering")
        return None

    plt.figure(figsize=(8,5))
    plt.plot(n_list, think_list, marker='o', linestyle='-')
    plt.xlabel('N (clients)')
    plt.ylabel('Inferred Think Time (s)')
    title = 'Inferred Think Time vs N'
    if source_desc:
        title += f" ({source_desc})"
    plt.title(title)
    plt.grid(True)

    fname = outdir / 'plot_InferredThinkTime_vs_N.png'
    plt.savefig(fname, bbox_inches='tight')
    if show:
        plt.show()
    plt.close()

    print(f"Saved {fname}")
    return fname


def main():
    ap = argparse.ArgumentParser(description='Plot take-1.log style results vs N')
    ap.add_argument('--log', '-l', type=Path, default=Path('fake_take1.log'), help='log file path')
    ap.add_argument('--out', '-o', type=Path, default=Path('plots_take1'), help='output directory')
    ap.add_argument('--metrics', '-m', type=str, default=','.join(DEFAULT_METRICS),
                    help='comma-separated metric list to plot')
    ap.add_argument('--show', action='store_true', help='show plots interactively')
    args = ap.parse_args()

    try:
        df = parse_log(args.log)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(2)

    ensure_dir(args.out)

    if 'ResponseTime' not in df.columns and 'AvgLatency' in df.columns:
        df['ResponseTime'] = df['AvgLatency']

    csv_out = args.out / 'take1_parsed.csv'
    df.to_csv(csv_out, index=False)
    print(f"Saved parsed CSV to: {csv_out}")

    metrics = [m.strip() for m in args.metrics.split(',') if m.strip()]
    print(metrics)
    saved_plots = plot_metrics(df, metrics, args.out, show=args.show)

    resp_vs_tput = plot_response_vs_throughput(df, args.out, show=args.show)
    inferred_plot = plot_inferred_think_time(df, args.out, show=args.show)

    if saved_plots or resp_vs_tput or inferred_plot:
        print("Saved plots summary:")
        for p in (saved_plots or []):
            print(f"  {p}")
        if resp_vs_tput:
            print(f"  {resp_vs_tput}")
        if inferred_plot:
            print(f"  {inferred_plot}")
    else:
        print("No plots were produced.")

    print("Done.")


if __name__ == '__main__':
    main()
