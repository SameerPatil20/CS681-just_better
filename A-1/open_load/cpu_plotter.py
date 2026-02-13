import matplotlib.pyplot as plt

WINDOW = 5

times = []
usr_values = []
avg_usr = []

with open("mpstat.log", "r") as f:
    for line in f:
        line = line.strip()

        if not line or line.startswith("CPU"):
            continue

        parts = line.split()

        if parts[2] == "all":
            time = parts[0] + " " + parts[1]
            usr = float(parts[3])

            times.append(time)
            usr_values.append(usr)

            window_vals = usr_values[-WINDOW:]
            avg_usr.append(sum(window_vals) / len(window_vals))

plt.figure()
plt.plot(times, avg_usr)
plt.xlabel("Time")
plt.ylabel("%usr (5-sample moving average)")
plt.title("CPU %usr (Moving Average)")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("usr_moving_avg.png")
plt.close()
