#!/bin/bash

# assignment 1 setup
# ./websim --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 1 --max_threads 345 --quantum 10 --think_base 4000 --think_mean_exp 10 --retry_limit 0 --service_time_avg 30 --timeout_lower 30000 --timeout_upper 30010 >> out.log 2>&1

#constant karna mt bhulna service time ko


# "Usage: websim [OPTIONS]\n"
#     "  --users N\n"
#     "  --simtime T\n"
#     "  --warmup W\n"
#     "  --trace_on 0/1\n"
#     "  --num_cores N\n"
#     "  --max_threads N\n"
#     "  --thread_queue_limit N\n"
#     "  --quantum Q\n"
#     "  --context_switch_overhead X\n"
#     "  --think_base X\n"
#     "  --think_mean_exp X\n"
#     "  --closed_loop 0/1\n"
#     "  --retry_limit N\n"
#     "  --service_time_avg X\n"
#     "  --timeout_lower X\n"
#     "  --timeout_upper X\n"
#     "  --rng_seed N\n"
#     "  --trace_prefix STR\n"
#     " --service_time_dist STR\n"
#     " --sched_policy STR\n"
#clear  log
> out.log


cd simulator;make;cd ..;
for users in $(seq 10 20 295)
do
    echo "Running simulation with users=$users" >> out.log

    # ./simulator/websim  --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 4 --max_threads 256 --thread_queue_limit 15000 --quantum 10 --think_base 3000 --context_switch_overhead 0.2 --think_mean_exp 200 --retry_limit 0 --service_time_avg 60 --timeout_lower 20000 --timeout_upper 30000 --rng_seed $users >> out.log 2>&1
     ./simulator/websim --service_time_dist constant --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 1 --max_threads 345 --quantum 10 --think_base 4000 --think_mean_exp 10 --retry_limit 0 --service_time_avg 30 --timeout_lower 30000 --timeout_upper 30010 >> out.log 2>&1

    # ./websim --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 4 --max_threads 256 --thread_queue_limit 15000 --quantum 10 --think_base 3000 --context_switch_overhead 0.2 --think_mean_exp 200 --retry_limit 0\
    # --service_time_avg 100 --service_time_dist uniform --timeout_lower 20000 --timeout_upper 30000 --rng_seed $users --sched_policy SJF >> out.log 2>&1
    
    echo "--------------------------------------" >> out.log
done
cd simulator;make clean;cd ..;

