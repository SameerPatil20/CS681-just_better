import os
import matplotlib.pyplot as plt

OUT_DIR = "plots"
os.makedirs(OUT_DIR, exist_ok=True)

rates = []
throughputs = []
avg_latencies = []
failed = []
completed = []

with open("final_output_copy.log", "r") as f:
    lines = f.readlines()

i = 0
while i < len(lines):
    line = lines[i].strip()

    if line.startswith("rate:"):
        rate = int(line.split(":")[1])

        completed_req = int(lines[i+2].split(":")[1])
        failed_req = int(lines[i+3].split(":")[1])
        throughput = float(lines[i+4].split(":")[1].split()[0])
        avg_latency = float(lines[i+5].split(":")[1].split()[0])

        rates.append(rate)
        completed.append(completed_req)
        failed.append(failed_req)
        throughputs.append(throughput)
        avg_latencies.append(avg_latency)

        i += 6
    else:
        i += 1

cpu_usage = [25.21472222222222, 39.158722222222224, 49.28169398907104, 54.64737704918032, 63.82747252747253, 68.17934065934065, 73.02559782608695, 80.49192307692309, 87.73657458563535, 94.40247311827957, 95.03360215053763, 94.87695187165777, 94.74085561497327, 96.1629891304348, 95.68702702702701, 95.59989189189189, 96.57912568306011, 96.20673913043478, 96.37429347826087, 95.82043243243243]
plt.figure()
plt.plot(throughputs, cpu_usage, marker='o')
plt.xlabel("Throughput (req/s)")
plt.ylabel("CPU %usr")
plt.title("CPU %usr vs Throughput")
plt.grid(True)
plt.savefig(f"{OUT_DIR}/cpu_vs_throughput.png", dpi=300, bbox_inches="tight")
plt.close()


print(f"Plots saved in ./{OUT_DIR}/")
