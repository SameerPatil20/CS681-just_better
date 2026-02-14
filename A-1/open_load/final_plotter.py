import os
import matplotlib.pyplot as plt

OUT_DIR = "plots"
os.makedirs(OUT_DIR, exist_ok=True)

rates = []
throughputs = []
avg_latencies = []
failed = []
completed = []

with open("final_output.log", "r") as f:
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

plt.figure()
plt.plot(rates, avg_latencies, marker='o')
plt.xlabel("Rate (req/s)")
plt.ylabel("Average Response Time (s)")
plt.title("Response Time vs Rate")
plt.grid(True)
plt.savefig(f"{OUT_DIR}/response_time_vs_rate.png", dpi=300, bbox_inches="tight")
plt.close()

plt.figure()
plt.plot(rates, throughputs, marker='o')
plt.xlabel("Rate (req/s)")
plt.ylabel("Throughput (req/s)")
plt.title("Throughput vs Rate")
plt.grid(True)
plt.savefig(f"{OUT_DIR}/throughput_vs_rate.png", dpi=300, bbox_inches="tight")
plt.close()


plt.figure()
plt.plot(throughputs, failed, marker='o')
plt.xlabel("Throughput (req/s)")
plt.ylabel("Failed Requests")
plt.title("Failed Requests vs Throughput")
plt.grid(True)
plt.savefig(f"{OUT_DIR}/failed_vs_throughput.png", dpi=300, bbox_inches="tight")
plt.close()

plt.figure()
plt.plot(rates, completed, marker='o')
plt.xlabel("Rate (req/s)")
plt.ylabel("Completed Requests")
plt.title("Completed Requests vs Rate")
plt.grid(True)
plt.savefig(f"{OUT_DIR}/completed_vs_rate.png", dpi=300, bbox_inches="tight")
plt.close()

plt.figure()
plt.plot(rates, completed, marker='o', label='Completed Requests')
plt.plot(rates, failed, marker='o', label='Failed Requests')
plt.xlabel("Rate (req/s)")
plt.ylabel("Number of Requests")
plt.title("Completed and Failed Requests vs Rate")
plt.legend()
plt.grid(True)
plt.savefig(f"{OUT_DIR}/completed_failed_vs_rate.png", dpi=300, bbox_inches="tight")
plt.close()

plt.figure()
plt.plot(rates, [throughputs[i]*avg_latencies[i] for i in range(len(rates))], marker='o')
plt.xlabel("Rate (req/s)")
plt.ylabel("Throughput * Latency")
plt.title("Throughput * Latency vs Rate")
plt.grid(True)
plt.savefig(f"{OUT_DIR}/throughput_latency_vs_rate.png", dpi=300, bbox_inches="tight")
plt.close()

print([throughputs[i]*avg_latencies[i] for i in range(len(rates))])
print(f"Plots saved in ./{OUT_DIR}/")
