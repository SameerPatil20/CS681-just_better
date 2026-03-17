#!/usr/bin/env python3
import argparse

THINK=0

def run_mva(N_max, S_ms, Z_ms):
    global THINK
    Q_prev=0.0
    for n in range(1, N_max+1):
        R_delay=Z_ms
        R_server=S_ms*(1.0+Q_prev)
        R_total=R_delay+R_server
        X=n / R_total
        X_sec=X*1000.0
        util=X*S_ms
        Q_curr=X*R_server
        print(f"Users={n} ResponseTime={(R_total-THINK):.6f} Throughput={X_sec:.6f}  Util={util:.6f}")
        Q_prev=Q_curr


if __name__ == "__main__":
    # global THINK
    parser=argparse.ArgumentParser()
    parser.add_argument("--users_max", type=int, required=True)
    parser.add_argument("--service_time_avg", type=float, required=True)
    parser.add_argument("--overhead_ms", type=float, default=0.0)
    parser.add_argument("--quantum", type=float, default=10.0)
    parser.add_argument("--use_quantum", type=int, default=0)
    parser.add_argument("--think_base", type=float, required=True)
    parser.add_argument("--think_mean_exp", type=float, required=True)
    args=parser.parse_args()
    Z_ms=args.think_base+args.think_mean_exp
    THINK = args.think_base
    if args.use_quantum:
        num_quanta=args.service_time_avg / args.quantum
        S_ms=args.service_time_avg+num_quanta*args.overhead_ms
    else:
        S_ms=args.service_time_avg+args.overhead_ms

    run_mva(args.users_max, S_ms, Z_ms)