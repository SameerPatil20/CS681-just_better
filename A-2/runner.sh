#!/bin/bash

# assignment 1 setup
# ./websim --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 1 --max_threads 345 --quantum 10 --think_base 4000 --think_mean_exp 10 --retry_limit 0 --service_time_avg 30 --timeout_lower 30000 --timeout_upper 30010 >> out.log 2>&1



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
# Clear previous log
> out.log

make
for users in $(seq 2 10 300)
do
    echo "Running simulation with users=$users" >> out.log
    
    ./websim --users $users --simtime 180000 --warmup 20000 --trace_on 0 --num_cores 1 --max_threads 345 --quantum 10 --think_base 4000 --think_mean_exp 10 --retry_limit 0 --service_time_avg 30 --timeout_lower 30000 --timeout_upper 30010 >> out.log 2>&1
    
    echo "--------------------------------------" >> out.log
done
make clean