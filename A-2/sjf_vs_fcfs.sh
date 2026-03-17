#!/bin/bash

> ./SJF_vs_FCFS/SJF_out.log
> ./SJF_vs_FCFS/FCFS_out.log

make
for users in $(seq 5 10 3000)
do
    echo "Running simulation with users=$users" >> ./SJF_vs_FCFS/FCFS_out.log
    
    ./websim --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 4 --max_threads 256 --thread_queue_limit 15000 --quantum 10 --think_base 3000 --context_switch_overhead 0.2 --think_mean_exp 200 --retry_limit 0\
    --service_time_avg 60 --service_time_dist uniform --timeout_lower 20000 --timeout_upper 30000 --rng_seed $users --sched_policy FCFS >> ./SJF_vs_FCFS/FCFS_out.log 2>&1
    
    echo "--------------------------------------" >> ./SJF_vs_FCFS/FCFS_out.log
done

for users in $(seq 5 10 3000)
do
    echo "Running simulation with users=$users" >> ./SJF_vs_FCFS/SJF_out.log
    
    ./websim --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 4 --max_threads 256 --thread_queue_limit 15000 --quantum 100 --think_base 3000 --context_switch_overhead 1 --think_mean_exp 200 --retry_limit 0\
    --service_time_avg 60 --service_time_dist uniform --timeout_lower 20000 --timeout_upper 30000 --rng_seed $users --sched_policy SJF >> ./SJF_vs_FCFS/SJF_out.log 2>&1
    
    echo "--------------------------------------" >> ./SJF_vs_FCFS/SJF_out.log
done
make clean
