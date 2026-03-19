#!/bin/bash

> ./SJF_vs_RR/SJF_out.log
> ./SJF_vs_RR/RR_out.log

cd simulator;make;cd ..;
for users in $(seq 5 10 8000)
do
    echo "Running simulation with users=$users" >> ./SJF_vs_RR/RR_out.log
    
    ./simulator/websim --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 4 --max_threads 256 --thread_queue_limit 15000 --quantum 10 --think_base 3000 --context_switch_overhead 0.2 --think_mean_exp 200 --retry_limit 0\
    --service_time_avg 60 --service_time_dist exponential --timeout_lower 20000 --timeout_upper 30000 --rng_seed $users --sched_policy RR >> ./SJF_vs_RR/RR_out.log 2>&1
    
    echo "--------------------------------------" >> ./SJF_vs_RR/RR_out.log
done

for users in $(seq 5 10 8000)
do
    echo "Running simulation with users=$users" >> ./SJF_vs_RR/SJF_out.log
    
    ./simulator/websim --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 4 --max_threads 256 --thread_queue_limit 15000 --quantum 100 --think_base 3000 --context_switch_overhead 0.2 --think_mean_exp 200 --retry_limit 0\
    --service_time_avg 60 --service_time_dist exponential --timeout_lower 20000 --timeout_upper 30000 --rng_seed $users --sched_policy SJF >> ./SJF_vs_RR/SJF_out.log 2>&1
    
    echo "--------------------------------------" >> ./SJF_vs_RR/SJF_out.log
done
cd simulator;make clean;cd ..;
cd SJF_vs_RR/; python3 plotter.py; cd ../