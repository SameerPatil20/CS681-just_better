#!/bin/bash

SIMTIME=180000
WARMUP=20000
TRACE_ON=0
NUM_CORES=4
MAX_THREADS=256
THREAD_QUEUE_LIMIT=15000
QUANTUM=10
THINK_BASE=3000
CONTEXT_SWITCH_OVERHEAD=0.2
THINK_MEAN_EXP=200
RETRY_LIMIT=0
SERVICE_TIME_AVG=60
SERVICE_TIME_DIST="exponential"
TIMEOUT_LOWER=20000
TIMEOUT_UPPER=30000

NUM_RUNS=40
OUTDIR="confidence_interval"
mkdir -p "${OUTDIR}"

START=40
STEP=40
END=3000

echo "Building project..."

cd ./simulator;make;cd ..;


for runidx in $(seq 1 ${NUM_RUNS}); do
    outfile="${OUTDIR}/run_${runidx}.log"
    > $outfile
    echo "=== RUN FILE ${outfile} (run index = ${runidx}) ===" > "${outfile}"
    echo "Run file created: ${outfile}"

    for users in $(seq ${START} ${STEP} ${END}); do
        seed=${runidx}
        entry_header="### ENTRY users=${users} run=${runidx} seed=${seed} ###"
        echo "${entry_header}" >> "${outfile}"
        # echo "  [run ${runidx}] running users=${users} -> ${outfile}"
        ./simulator/websim \
            --users ${users} \
            --simtime ${SIMTIME} \
            --warmup ${WARMUP} \
            --trace_on ${TRACE_ON} \
            --num_cores ${NUM_CORES} \
            --max_threads ${MAX_THREADS} \
            --thread_queue_limit ${THREAD_QUEUE_LIMIT} \
            --quantum ${QUANTUM} \
            --think_base ${THINK_BASE} \
            --context_switch_overhead ${CONTEXT_SWITCH_OVERHEAD} \
            --think_mean_exp ${THINK_MEAN_EXP} \
            --closed_loop 1 \
            --retry_limit ${RETRY_LIMIT} \
            --service_time_avg ${SERVICE_TIME_AVG} \
            --service_time_dist ${SERVICE_TIME_DIST} \
            --timeout_lower ${TIMEOUT_LOWER} \
            --timeout_upper ${TIMEOUT_UPPER} \
            --rng_seed ${seed} \
            --sched_policy RR \
            >> "${outfile}" 2>&1
        echo "### END_ENTRY users=${users} run=${runidx} ###" >> "${outfile}"
        echo "" >> "${outfile}"
    done

    echo "Completed run file: ${outfile}"
done
echo "All ${NUM_RUNS} run files generated in ${OUTDIR}/ (each contains all users values)."
cd ./simulator;make clean;cd ..;