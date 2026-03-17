#!/usr/bin/env python3
"""
mix_plot.py

Parse mixed log formats (out.log and take-*.log) and plot Throughput and Response Time.
Usage:
    python3 mix_plot.py file1 file2 ...
"""
import re
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import os

# ---------------- format detection ----------------
def detect_format(filename):
    """Return 'out' or 'take' or 'unknown' using strict checks."""
    has_run = False
    has_n = False
    has_throughput = False
    with open(filename, 'r', errors='ignore') as fh:
        for _ in range(60):  # check first up-to-60 lines for robust detection
            line = fh.readline()
            if not line:
                break
            low = line.lower()
            print(line)
            if 'RUN:' in line:
                has_run = True
            if re.search(r'\b[nN]\s*=', line):
                has_n = True
            if 'throughput' in low:
                has_throughput = True

    if has_run:
        return 'out'
    if has_n and has_throughput:
        return 'take'
    return 'unknown'


# ---------------- parse out.log ----------------
def parse_out_format(filename):
    """
    Parse files like:
       Running simulation with users=12
       RUN: avg_rt=30.4 throughput=0.0005 ...
    Returns DataFrame with columns M, throughput, response_time (or None if nothing)
    """
    rows = []
    current_M = None
    with open(filename, 'r', errors='ignore') as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue

            # users may appear anywhere before the RUN line
            m_users = re.search(r'users=(\d+)', line, re.IGNORECASE)
            if m_users:
                current_M = int(m_users.group(1))

            if 'RUN:' in line:
                # avg_rt and throughput are expected on the RUN line
                rt_m = re.search(r'avg_rt=([0-9.eE+-]+)', line, re.IGNORECASE)
                thr_m = re.search(r'throughput=([0-9.eE+-]+)', line, re.IGNORECASE)

                # Accept the row if M is known and at least one metric present.
                if current_M is not None and (rt_m or thr_m):
                    rt_val = float(rt_m.group(1)) if rt_m else float('nan')
                    thr_val = float(thr_m.group(1)) if thr_m else float('nan')
                    rows.append({'M': current_M, 'throughput': thr_val, 'response_time': rt_val})

    df = pd.DataFrame(rows)
    if df.empty:
        print(f"{filename}: ERROR parsing OUT format (no rows found)")
        return None
    return df


# ---------------- parse take format ----------------
def parse_take_format(filename):
    """
    Parse files like:
      N=10 Throughput=2.41111 AvgLatency=0.15081 ...
    This handles case differences and keys like AvgLatency, AvgLatency=, etc.
    """
    rows = []
    with open(filename, 'r', errors='ignore') as fh:
        for raw in fh:
            line = raw.strip()
            if not line:
                continue
            # N=10 (case-insensitive)
            m_n = re.search(r'\bN\s*=\s*(\d+)\b', line, re.IGNORECASE)
            # Throughput=...
            m_thr = re.search(r'Throughput\s*=\s*([0-9.eE+-]+)', line, re.IGNORECASE)
            # AvgLatency= or AvgLatency or Latency= or Response=
            m_rt = re.search(r'(?:AvgLatency|AvgLatency|Latency|Response|Response_time|Avg_rt)\s*=\s*([0-9.eE+-]+)', line, re.IGNORECASE)

            if m_n and m_thr and m_rt:
                try:
                    M = int(m_n.group(1))
                    thr = float(m_thr.group(1))
                    rt = float(m_rt.group(1))
                    rows.append({'M': M, 'throughput': thr, 'response_time': rt})
                except Exception:
                    # skip malformed conversions
                    continue

    df = pd.DataFrame(rows)
    if df.empty:
        # Try a more flexible fallback: accept lines where N and throughput exist and latency might be labelled differently
        rows = []
        with open(filename, 'r', errors='ignore') as fh:
            for raw in fh:
                line = raw.strip()
                if not line:
                    continue
                m_n = re.search(r'\bN\s*=\s*(\d+)\b', line, re.IGNORECASE)
                m_thr = re.search(r'Throughput\s*=\s*([0-9.eE+-]+)', line, re.IGNORECASE)
                # try AvgLatency or P95 as a fallback (prefer AvgLatency)
                m_rt_any = re.search(r'avglatency\s*=\s*([0-9.eE+-]+)', line, re.IGNORECASE) \
                           or re.search(r'avg_rt\s*=\s*([0-9.eE+-]+)', line, re.IGNORECASE) \
                           or re.search(r'\bresponse\b\s*=\s*([0-9.eE+-]+)', line, re.IGNORECASE)
                if m_n and m_thr and m_rt_any:
                    try:
                        rows.append({'M': int(m_n.group(1)),
                                     'throughput': float(m_thr.group(1)),
                                     'response_time': float(m_rt_any.group(1))})
                    except Exception:
                        continue
        df = pd.DataFrame(rows)

    if df.empty:
        print(f"{filename}: ERROR parsing TAKE format (no rows found). First 8 lines for debug:")
        with open(filename, 'r', errors='ignore') as fh:
            for i in range(8):
                l = fh.readline()
                if not l:
                    break
                print("  " + l.rstrip())
        return None

    return df


# ---------------- unified parse ----------------
def parse_file(filename):
    fmt = detect_format(filename)
    if fmt == 'out':
        print(f"{filename}: detected format = OUT")
        df = parse_out_format(filename)
    elif fmt == 'take':
        print(f"{filename}: detected format = TAKE")
        df = parse_take_format(filename)
    else:
        print(f"{filename}: detected format = UNKNOWN -> skipping")
        return None

    if df is None or df.empty:
        print(f"{filename}: no usable data after parsing -> skipping")
        return None

    # Ensure numeric columns exist and coerce them
    for col in ['throughput', 'response_time']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Group by M and take mean if multiple rows per M
    df = df.groupby('M', as_index=False).mean().sort_values('M')
    return df


# ---------------- plotting helpers ----------------
def short_label(path):
    # friendly label for legend: filename (no directory)
    return os.path.basename(path)


def plot_metric(files_data, metric, ylabel, title):
    plt.figure(figsize=(8, 5))
    any_plotted = False
    for fname, df in files_data.items():
        if df is None:
            continue
        if metric not in df.columns or df[metric].dropna().empty:
            print(f"{fname}: no '{metric}' data -> skipping on this plot")
            continue
        any_plotted = True
        plt.plot(df['M'], df[metric], marker='o', label=short_label(fname))
    if not any_plotted:
        print(f"No file had '{metric}' data. Skipping {title} plot.")
        return
    plt.xlabel('M (users / N)')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()


# ---------------- main ----------------
def main(args):
    if not args:
        print("Usage: python3 mix_plot.py file1 file2 ...")
        sys.exit(1)

    files = args
    files_data = {}
    for f in files:
        p = Path(f)
        if not p.exists():
            print(f"{f}: file not found -> skipping")
            files_data[f] = None
            continue
        df = parse_file(f)
        files_data[f] = df

    # Plot throughput (only files that have throughput)
    plot_metric(files_data, 'throughput', 'Throughput', 'Throughput vs M (one curve per file)')

    # Plot response_time (only files that have response_time / AvgLatency)
    plot_metric(files_data, 'response_time', 'Response Time (s)', 'Response Time vs M (one curve per file)')

    plt.show()


if __name__ == "__main__":
    main(sys.argv[1:])