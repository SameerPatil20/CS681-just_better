import re
import os
import matplotlib.pyplot as plt

os.makedirs("plots", exist_ok=True)

users = []
avg_rt = []
throughput = []
goodput = []
badput = []
timeouts = []
util = []

current_users = None

with open("out.log") as f:
    for line in f:
        m = re.search(r'users=(\d+)', line, re.IGNORECASE)
        if m:
            current_users = int(m.group(1))
        m = re.search(
            r'ResponseTime=([\d\.]+).*Throughput=([\d\.]+).*goodput=([\d\.]+).*badput=([\d\.]+).*timedout=(\d+).*Util=([\d\.]+)',
            line
        )
        if m and current_users is not None:
            users.append(current_users)
            avg_rt.append(float(m.group(1)))
            throughput.append(float(m.group(2)))
            goodput.append(float(m.group(3)))
            badput.append(float(m.group(4)))
            timeouts.append(int(m.group(5)))
            util.append(float(m.group(6)))

plt.figure()
plt.plot(users, avg_rt)
plt.xlabel("Number of Users")
plt.ylabel("Average Response Time")
plt.title("Average Response Time vs Users")
plt.grid(True)
plt.savefig("plots/avg_response_time.png")

plt.figure()
plt.plot(users, throughput)
plt.xlabel("Number of Users")
plt.ylabel("Throughput(in req/sec)")
plt.title("Throughput vs Users")
plt.grid(True)
plt.savefig("plots/throughput.png")

plt.figure()
plt.plot(users, goodput)
plt.xlabel("Number of Users")
plt.ylabel("Goodput(in req/sec)")
plt.title("Goodput vs Users")
plt.grid(True)
plt.savefig("plots/goodput.png")

plt.figure()
plt.plot(users, badput)
plt.xlabel("Number of Users")
plt.ylabel("Badput(in req/sec)")
plt.title("Badput vs Users")
plt.grid(True)
plt.savefig("plots/badput.png")

plt.figure()
plt.plot(users, timeouts)
plt.xlabel("Number of Users")
plt.ylabel("Timeouts")
plt.title("Timeouts vs Users")
plt.grid(True)
plt.savefig("plots/timeouts.png")

plt.figure()
plt.plot(users, util)
plt.xlabel("Number of Users")
plt.ylabel("Utilization")
plt.title("Utilization vs Users")
plt.grid(True)
plt.savefig("plots/utilization.png")

plt.figure()
plt.plot(users, throughput, color='blue', linestyle='-', linewidth=2, label="Throughput")
plt.plot(users, goodput, color='green', linestyle='--', linewidth=2, label="Goodput")
plt.plot(users, badput, color='red', linestyle=':', linewidth=2, label="Badput")

plt.xlabel("Number of Users")
plt.ylabel("Requests / sec")
plt.title("Throughput, Goodput and Badput vs Users")
plt.grid(True)
plt.legend()
plt.savefig("plots/throughput_goodput_badput.png")
