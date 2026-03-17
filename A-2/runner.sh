#!/bin/bash

# Clear previous log
> out.log

make
for users in $(seq 5 5 1000)
do
    echo "Running simulation with users=$users" >> out.log
    
    ./websim --users $users --simtime 20000 --warmup 1000 --trace_on 1 >> out.log 2>&1
    
    echo "--------------------------------------" >> out.log
done
make clean