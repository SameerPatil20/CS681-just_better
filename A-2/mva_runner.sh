#!/bin/bash

# assignment 1 setup
# python3 mva.py --users_max $users --service_time_avg 30 --overhead_ms 0.2 --quantum 10 --use_quantum 1 --think_base 4000 --think_mean_exp 10
> mva_out.log

# make
# for users in $(seq 2 10 300)
# do
#     # echo "Running simulation with users=$users" >> mva_out.log
    
python3 mva.py --users_max 300 --service_time_avg 30 --overhead_ms 0.2 --quantum 10 --use_quantum 0 --think_base 4000 --think_mean_exp 10 >> mva_out.log 2>&1
    
    # echo "--------------------------------------" >> out.log
# done
# make clean