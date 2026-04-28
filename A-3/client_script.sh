# echo "ArrivalRate,device_write,cpus,memory,cpuLoad,Throughput,ResponseTime" > loadtest.csv

# for device_write in "10mb" "20mb"
# do
#     for cpu in 0.5 1 2
#     do
#         for mem in '500m' '600m'
#         do
#             for arr in {10..400..10};
#             do
#                 for size in {100..800..50};
#                 do
#                     for cpuLoad in 350 400 450 500
#                     do
#                     	curl -X GET "http://127.0.0.1:8080/dockerStart.php?memory=${mem}&cpus=${cpu}&device-write=${device_write}"
#                     	httperf --client=0/1 --server=127.0.0.1 --port=80 --uri="/server.php?size=${size}&cpuLoad=${cpuLoad}" --send-buffer=4096 --recv-buffer=16384 --num-conns=5000 --rate=${arr} > result.txt
#                     	awk -v var0="$arr" -v var1="$device_write" -v var2="$cpu" -v var3="$mem" -v var4="$cpuLoad" '{OFS=","; if ($1 == "Reply" && $2 == "rate") t=$7; if ($1 == "Reply" && $2 == "time") r1 = $5;} END{print var0,var1,var2,var3,var4,t,r1}' result.txt >> loadtest.csv
#                     	curl -X GET "http://127.0.0.1:8080/dockerStop.php"
#                 	done
#                 done
#             done                
#         done	
#     done
# done


#!/usr/bin/env bash
set -euo pipefail

g++ -std=c++17 -O2 -pthread loader.cpp -o loadgenerator

echo "ArrivalRate,device_write,cpus,memory,size,cpuLoad,num-request,workers,Throughput,ServiceTime,ResponseTimeMs,P90ResponseTimeMs,Completed" > loadtest.csv

SERVER_IP="10.130.152.31"

for device_write in "15mb" "20mb" "30mb"; do
  for cpu in 0.5 1 2; do
    for mem in "500m"; do
      for arr in $(seq 12 2 20); do
        for size in $(seq 2000 2000 8000); do
          for cpuLoad in $(seq 200000 500000 1700000); do # 20ms to 170 ms
          echo "Testing with device_write=${device_write}, cpu=${cpu}, mem=${mem}, arrival_rate=${arr}, size=${size}, cpuLoad=${cpuLoad}"
            curl -X GET "http://${SERVER_IP}:8080/dockerStop.php"
            echo "${device_write} ${cpu} ${mem} ${arr} ${size} ${cpuLoad}"> out.log
            curl -X GET "http://${SERVER_IP}:8080/dockerStart.php?memory=${mem}&cpus=${cpu}&device-write=${device_write}"
            ./loadgenerator \
              --device-write "${device_write}" \
              --cpus "${cpu}" \
              --memory "${mem}" \
              --arrival-rate "${arr}" \
              --size "${size}" \
              --cpuLoad "${cpuLoad}" \
              --num-requests 400 \
              --workers 100 \
              --csv loadtest.csv \
              --server-host "${SERVER_IP}" \
              --admin-host "${SERVER_IP}" \
              --server-port 8090 \
              --admin-port 8080

            echo "closing container"
            # exit
            curl -X GET "http://${SERVER_IP}:8080/dockerStop.php"
          done
        done
      done
    done
  done
done  

# 10000-> 1ms cpu load
# 100 size -> 100kb data read/write

# for device_write in "10mb" "20mb" "30mb"; do
#   for cpu in 0.5; do
#     for mem in "500m"; do
#       for arr in $(seq 10 2000 400); do
#         for size in $(seq 1000 100000 80000); do
#           for cpuLoad in $(seq 1 50000000 5000000); do
#           echo "Testing with device_write=${device_write}, cpu=${cpu}, mem=${mem}, arrival_rate=${arr}, size=${size}, cpuLoad=${cpuLoad}"
#             curl -X GET "http://${SERVER_IP}:8080/dockerStop.php"
#             echo "${device_write} ${cpu} ${mem} ${arr} ${size} ${cpuLoad}"> out.log
#             curl -X GET "http://${SERVER_IP}:8080/dockerStart.php?memory=${mem}&cpus=${cpu}&device-write=${device_write}"
#             ./loadgenerator \
#               --device-write "${device_write}" \
#               --cpus "${cpu}" \
#               --memory "${mem}" \
#               --arrival-rate "${arr}" \
#               --size "${size}" \
#               --cpuLoad "${cpuLoad}" \
#               --num-requests 500 \
#               --workers 20 \
#               --csv loadtest.csv \
#               --server-host "${SERVER_IP}" \
#               --admin-host "${SERVER_IP}" \
#               --server-port 8090 \
#               --admin-port 8080

#             echo "closing container"
#             # curl -X GET "http://${SERVER_IP}:8080/dockerStop.php"
#           done
#         done
#       done
#     done
#   done
# done  
