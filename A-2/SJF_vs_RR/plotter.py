import glob
import os
import re
from collections import defaultdict

import matplotlib.pyplot as plt


def parse_log(file_path):
    """
    Parse one simulator log.
    Expected structure:
      Running simulation with users=<N> run=<R>
      <metrics line containing key=value pairs>
      --------------------------------------
    Returns:
      { users: {metric: value, ...}, ... }
    """
    data = {}
    current_user = None

    with open(file_path, "r") as f:
        for raw_line in f:
            line = raw_line.strip()

            m = re.match(r"Running simulation with users=(\d+)", line)
            if m:
                current_user = int(m.group(1))
                continue

            if current_user is None:
                continue

            metrics = {}
            for part in line.split():
                if "=" in part:
                    key, value_str = part.split("=", 1)
                    try:
                        metrics[key] = float(value_str)
                    except ValueError:
                        pass

            if metrics:
                data[current_user] = metrics
                current_user = None

    return data


def average_logs(log_files):
    """
    Average metrics across multiple run logs.
    Returns:
      { users: {metric: avg_value, ...}, ... }
    """
    agg = defaultdict(lambda: defaultdict(list))

    for file_path in log_files:
        run_data = parse_log(file_path)
        for users, metrics in run_data.items():
            for key, value in metrics.items():
                agg[users][key].append(value)

    averaged = {}
    for users, metric_map in agg.items():
        averaged[users] = {
            key: sum(values) / len(values)
            for key, values in metric_map.items()
            if values
        }

    return averaged


def plot_metric(users, rr_data, sjf_data, metric, filename, ylabel=None):
    rr_values = [rr_data.get(u, {}).get(metric, 0.0) for u in users]
    sjf_values = [sjf_data.get(u, {}).get(metric, 0.0) for u in users]

    plt.figure(figsize=(10, 6))
    plt.plot(users, rr_values, label="RR", linestyle="-")
    plt.plot(users, sjf_values, label="SJF", linestyle="--")
    plt.xlabel("Number of Users")
    plt.ylabel(ylabel if ylabel else metric)
    plt.title(f"{metric} vs Number of Users (RR vs SJF) — Average of 10 Runs")
    plt.legend()
    plt.grid(True)
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()


def main():
    rr_logs = sorted(glob.glob(os.path.join("RR_logs", "RR_run*.log")))
    sjf_logs = sorted(glob.glob(os.path.join("SJF_logs", "SJF_run*.log")))

    if not rr_logs:
        raise FileNotFoundError("No RR logs found in RR_logs/")
    if not sjf_logs:
        raise FileNotFoundError("No SJF logs found in SJF_logs/")

    rr_avg = average_logs(rr_logs)
    sjf_avg = average_logs(sjf_logs)

    users = sorted(set(rr_avg.keys()) | set(sjf_avg.keys()))

    parameters = [
        "ResponseTime",
        "Throughput",
        "goodput",
        "badput",
        "completed",
        "timedout",
        "dropped",
        "Util",
    ]

    for param in parameters:
        plot_metric(
            users,
            rr_avg,
            sjf_avg,
            param,
            f"{param}_vs_users.png",
        )

    # Combined plot for throughput, goodput, badput
    plt.figure(figsize=(10, 6))
    metrics = ["goodput", "badput", "Throughput"]
    styles = {
        "RR": {"linestyle": "-"},
        "SJF": {"linestyle": "--"},
    }

    for metric in metrics:
        rr_values = [rr_avg.get(u, {}).get(metric, 0.0) for u in users]
        sjf_values = [sjf_avg.get(u, {}).get(metric, 0.0) for u in users]

        plt.plot(users, rr_values, label=f"RR {metric}", **styles["RR"])
        plt.plot(users, sjf_values, label=f"SJF {metric}", **styles["SJF"])

    plt.xlabel("Number of Users")
    plt.ylabel("Value")
    plt.title("Throughput, Goodput, Badput vs Number of Users (Average of 10 Runs)")
    plt.legend()
    plt.grid(True)
    plt.savefig("combined_throughput_goodput_badput_vs_users.png", dpi=300, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    main()