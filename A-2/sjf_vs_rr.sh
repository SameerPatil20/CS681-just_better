#!/bin/bash
set -euo pipefail

OUTDIR="./SJF_vs_RR"
RR_DIR="$OUTDIR/RR_logs"
SJF_DIR="$OUTDIR/SJF_logs"

mkdir -p "$RR_DIR" "$SJF_DIR"

make -C simulator

for run in $(seq 1 5); do
    rr_log="$RR_DIR/RR_run${run}.log"
    : > "$rr_log"

    for users in $(seq 5 10 1000); do
        echo "Running simulation with users=$users run=$run" >> "$rr_log"

        seed=$((users * 1000 + run))

        ./simulator/websim \
            --users "$users" \
            --simtime 180000 \
            --warmup 20000 \
            --trace_on 0 \
            --num_cores 1 \
            --max_threads 256 \
            --thread_queue_limit 300 \
            --quantum 10 \
            --think_base 3000 \
            --context_switch_overhead 0.2 \
            --think_mean_exp 200 \
            --retry_limit 0 \
            --service_time_avg 60 \
            --service_time_dist exponential \
            --timeout_lower 20000 \
            --timeout_upper 30000 \
            --rng_seed "$seed" \
            --sched_policy RR >> "$rr_log" 2>&1

        echo "--------------------------------------" >> "$rr_log"
    done
done

for run in $(seq 1 5); do
    sjf_log="$SJF_DIR/SJF_run${run}.log"
    : > "$sjf_log"

    for users in $(seq 5 10 1000); do
        echo "Running simulation with users=$users run=$run" >> "$sjf_log"

        seed=$((users * 1000 + run))

        ./simulator/websim \
            --users "$users" \
            --simtime 180000 \
            --warmup 20000 \
            --trace_on 0 \
            --num_cores 1 \
            --max_threads 256 \
            --thread_queue_limit 15000 \
            --quantum 100 \
            --think_base 3000 \
            --context_switch_overhead 0.2 \
            --think_mean_exp 200 \
            --retry_limit 0 \
            --service_time_avg 60 \
            --service_time_dist exponential \
            --timeout_lower 20000 \
            --timeout_upper 30000 \
            --rng_seed "$seed" \
            --sched_policy SJF >> "$sjf_log" 2>&1

        echo "--------------------------------------" >> "$sjf_log"
    done
done

cd ./simulator
make clean
cd ..

cd "$OUTDIR"
python3 plotter.py
cd ..