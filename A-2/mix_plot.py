import sys
import re
import matplotlib.pyplot as plt

def parse_file(filename):
    M = []
    throughput = []
    response_time = []

    with open(filename, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # -------- FORMAT 1 --------
        if "Running simulation with users=" in line:
            # Extract M
            m = int(re.search(r'users=(\d+)', line).group(1))

            # Next line contains metrics
            if i + 1 < len(lines):
                next_line = lines[i + 1]

                rt_match = re.search(r'ResponseTime=([\d\.]+)', next_line)
                th_match = re.search(r'Throughput=([\d\.]+)', next_line)

                if rt_match and th_match:
                    M.append(m)
                    response_time.append(float(rt_match.group(1)))
                    throughput.append(float(th_match.group(1)))

            i += 2
            continue

        # -------- FORMAT 2 --------
        elif "Throughput=" in line and ("AvgLatency=" in line or "AvgLatency" in line):
            m_match = re.search(r'N=(\d+)', line)
            th_match = re.search(r'Throughput=([\d\.]+)', line)
            rt_match = re.search(r'AvgLatency=([\d\.]+)', line)

            if m_match and th_match and rt_match:
                M.append(int(m_match.group(1)))
                throughput.append(float(th_match.group(1)))
                response_time.append(float(rt_match.group(1)))

        i += 1

    return M, throughput, response_time


def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_results.py file1 file2 ...")
        sys.exit(1)

    files = sys.argv[1:]

    plt.figure(figsize=(12, 5))

    # -------- Throughput Plot --------
    plt.subplot(1, 2, 1)
    for file in files:
        M, th, _ = parse_file(file)
        plt.plot(M, th, marker='o', label=file)

    plt.xlabel("M (Users)")
    plt.ylabel("Throughput")
    plt.title("Throughput vs M")
    plt.legend()
    plt.grid()

    # -------- Response Time Plot --------
    plt.subplot(1, 2, 2)
    for file in files:
        M, _, rt = parse_file(file)
        plt.plot(M, rt, marker='o', label=file)

    plt.xlabel("M (Users)")
    plt.ylabel("Response Time / Latency")
    plt.title("Response Time vs M")
    plt.legend()
    plt.grid()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()