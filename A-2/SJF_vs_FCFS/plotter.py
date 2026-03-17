import matplotlib.pyplot as plt

def parse_log(file_path):
    data = {}
    with open(file_path, 'r') as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('Running simulation with users='):
                users = int(line.split('=')[1])
                i += 1
                if i < len(lines):
                    metrics_line = lines[i].strip()
                    parts = metrics_line.split()
                    metrics = {}
                    for part in parts:
                        if '=' in part:
                            key, value_str = part.split('=', 1)
                            try:
                                value = float(value_str)
                                metrics[key] = value
                            except ValueError:
                                pass
                    data[users] = metrics
            i += 1
    return data

fcfs_data = parse_log('FCFS_out.log')
sjf_data = parse_log('SJF_out.log')

users = sorted(fcfs_data.keys())

parameters = ['ResponseTime', 'Throughput', 'goodput', 'badput', 'completed', 'timedout', 'dropped', 'Util']

for param in parameters:
    plt.figure(figsize=(10, 6))
    fcfs_values = [fcfs_data[u].get(param, 0) for u in users]
    sjf_values = [sjf_data[u].get(param, 0) for u in users]
    
    plt.plot(users, fcfs_values, label='FCFS', linestyle='-')
    plt.plot(users, sjf_values, label='SJF', linestyle='--')
    
    plt.xlabel('Number of Users')
    plt.ylabel(param)
    plt.title(param + ' vs Number of Users (FCFS vs SJF)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig(param + '_vs_users.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Combined plot for goodput, badput, and Throughput for both FCFS and SJF
    metrics = ['goodput', 'badput', 'Throughput']
    colors = ['tab:blue', 'tab:orange', 'tab:red']
    markers = ['o', 's', '^']

    plt.figure(figsize=(10, 6))
    for idx, metric in enumerate(metrics):
        color = colors[idx % len(colors)]
        marker = markers[idx % len(markers)]
        fcfs_vals = [fcfs_data[u].get(metric, 0) for u in users]
        sjf_vals = [sjf_data[u].get(metric, 0) for u in users]

        plt.plot(users, fcfs_vals, label=f'FCFS {metric}', linestyle='-', color=color)
        plt.plot(users, sjf_vals, label=f'SJF {metric}', linestyle='--', color=color)

    plt.xlabel('Number of Users')
    plt.ylabel('Value')
    plt.title('Throughput, Goodput, Badput vs Number of Users (FCFS vs SJF)')
    plt.legend()
    plt.grid(True)
    plt.savefig('combined_throughput_goodput_badput_vs_users.png', dpi=300, bbox_inches='tight')
    plt.close()
