import matplotlib.pyplot as plt

LOW_THRESHOLD = 5.0   
GAP_LEN = 10          

blocks = []
current_block = []
low_count = 0

curr_len=0

with open("mpstat.log", "r") as f:
    for line in f:
        line = line.strip()

        if not line or line.startswith("CPU"):
            continue

        parts = line.split()

        if parts[2] == "all":
            usr = float(parts[3])

            if usr > LOW_THRESHOLD:
                current_block.append(usr)
                low_count = 0
                curr_len+=1
            else:
                low_count += 1

                if low_count >= GAP_LEN and current_block and curr_len>100:
                    blocks.append(current_block)
                    current_block = []
                    curr_len=0
if current_block:
    blocks.append(current_block)

block_avgs = [sum(block) / len(block) for block in blocks]
print("Block averages:", block_avgs, len(block_avgs))
block_avgs = block_avgs[:20]

plt.figure()
plt.plot(range(10, 201,10), block_avgs, marker='o')
plt.xlabel("Arrival rate (requests/sec)")
plt.ylabel("Average %usr")
plt.title("Average CPU %usr vs Arrival Rate")
plt.tight_layout()

plt.savefig("usr_block_averages.png")
plt.close()
