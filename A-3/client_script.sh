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

echo "ArrivalRate,device_write,cpus,memory,cpuLoad,Throughput,ResponseTimeMs,P90ResponseTimeMs,Completed" > loadtest.csv

SERVER_IP="10.130.152.75"

for device_write in "10mb" "20mb"; do
  for cpu in 0.5 1 2; do
    for mem in "500m" "600m" "800m"; do
      for arr in $(seq 10 20 400); do
        for size in $(seq 100 100 800); do
          for cpuLoad in $(seq 100 100 1000); do
            echo "${device_write} ${cpu} ${mem} ${arr} ${size} ${cpuLoad}"> out.log
            echo "sending curl"
            curl -X GET "http://${SERVER_IP}:8080/dockerStart.php?memory=${mem}&cpus=${cpu}&device-write=${device_write}"
            echo "done curl"
            ./loadgenerator \
              --device-write "${device_write}" \
              --cpus "${cpu}" \
              --memory "${mem}" \
              --arrival-rate "${arr}" \
              --size "${size}" \
              --cpuLoad "${cpuLoad}" \
              --num-requests 50 \
              --workers 20 \
              --csv loadtest.csv \
              --server-host "${SERVER_IP}" \
              --admin-host "${SERVER_IP}" \
              --server-port 80 \
              --admin-port 8080

            echo "closing container"
            curl -X GET "http://${SERVER_IP}:8080/dockerStop.php"
          done
        done
      done
    done
  done
done
