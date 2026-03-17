import re
import os
import matplotlib.pyplot as plt

# create plots directory if it doesn't exist
os.makedirs("plots", exist_ok=True)

users = []
avg_rt = []
throughput = []
goodput = []
badput = []
timeouts = []

with open("out.log") as f:
    for line in f:
        m = re.search(r'users=(\d+)', line)
        if m:
            current_users = int(m.group(1))

        m = re.search(
            r'avg_rt=([\d\.]+).*throughput=([\d\.]+).*goodput=([\d\.]+).*badput=([\d\.]+).*completed=\d+ timedout=(\d+)',
            line
        )
        if m:
            users.append(current_users)
            avg_rt.append(float(m.group(1)))
            throughput.append(float(m.group(2)))
            goodput.append(float(m.group(3)))
            badput.append(float(m.group(4)))
            timeouts.append(int(m.group(5)))
            # print(float(m.group(4)))

# Avg Response Time
plt.figure()
plt.plot(users, avg_rt, marker='o')
plt.xlabel("Number of Users")
plt.ylabel("Average Response Time")
plt.title("Average Response Time vs Users")
plt.grid(True)
plt.savefig("plots/avg_response_time.png")

# Throughput
plt.figure()
plt.plot(users, throughput, marker='o')
plt.xlabel("Number of Users")
plt.ylabel("Throughput")
plt.title("Throughput vs Users")
plt.grid(True)
plt.savefig("plots/throughput.png")

# Goodput
plt.figure()
plt.plot(users, goodput, marker='o')
plt.xlabel("Number of Users")
plt.ylabel("Goodput")
plt.title("Goodput vs Users")
plt.grid(True)
plt.savefig("plots/goodput.png")

# Badput
plt.figure()
plt.plot(users, badput, marker='o')
plt.xlabel("Number of Users")
plt.ylabel("Badput")
plt.title("Badput vs Users")
plt.grid(True)
plt.savefig("plots/badput.png")

# Timeouts
plt.figure()
plt.plot(users, timeouts, marker='o')
plt.xlabel("Number of Users")
plt.ylabel("Timeouts")
plt.title("Timeouts vs Users")
plt.grid(True)
plt.savefig("plots/timeouts.png")