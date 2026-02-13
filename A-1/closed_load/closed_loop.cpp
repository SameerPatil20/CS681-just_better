#include <curl/curl.h>
#include <thread>
#include <vector>
#include <atomic>
#include <chrono>
#include <iostream>
#include <algorithm>
#include <numeric>
#include <mutex>
#include <unistd.h>
#include <cstdlib>

using namespace std;
using namespace chrono;

const string SERVER_URL = "http://10.61.1.109/test.php";
const int DURATION = 180;      
const double THINK_TIME = 4;

atomic<int> success_cnt(0);
atomic<int> fail_cnt(0);
mutex lat_mutex;
vector<double> latencies;

size_t discard(void* ptr, size_t size, size_t nmemb, void* data) {
    return size * nmemb;
}

void client_worker(time_point<steady_clock> end_time) {
    double stagger = (rand() % 1000) / 1000.0 * THINK_TIME;
    this_thread::sleep_for(duration<double>(stagger));
    CURL* curl = curl_easy_init();
    if (!curl) return;
    vector<double> local_latencies;

    curl_easy_setopt(curl, CURLOPT_URL, SERVER_URL.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, discard);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 15L);

    while (steady_clock::now() < end_time) {
        auto start = steady_clock::now();
        CURLcode res = curl_easy_perform(curl);
        auto end = steady_clock::now();

        double latency = duration<double>(end - start).count();

        if (res == CURLE_OK) {
            success_cnt++;
            local_latencies.push_back(latency);
        } else {
            fail_cnt++;
        }
        this_thread::sleep_for(duration<double>(THINK_TIME));

    }
    {
        lock_guard<mutex> lock(lat_mutex);
        latencies.insert(latencies.end(), local_latencies.begin(), local_latencies.end());
    }

    curl_easy_cleanup(curl);
}

int main() {
    curl_global_init(CURL_GLOBAL_ALL);

    vector<int>users;
    for(int i=10;i<=300;i+=20){
        users.push_back(i);
    }


    for (int N : users) {
        success_cnt = 0;
        fail_cnt = 0;
        latencies.clear();

        auto end_time = steady_clock::now() + seconds(DURATION);
        vector<thread> threads;

        for (int i = 0; i < N; i++) {
            threads.emplace_back(client_worker, end_time);
        }

        for (auto& t : threads) t.join();

        double throughput = success_cnt / (double)DURATION;

        double avg_latency = accumulate(latencies.begin(), latencies.end(), 0.0)
                              / latencies.size();

        sort(latencies.begin(), latencies.end());
        double p95 = latencies[(int)(0.95 * latencies.size())];

        cout << "N=" << N
             << " Throughput=" << throughput
             << " AvgLatency=" << avg_latency
             << " P95=" << p95
             << " Failures=" << fail_cnt
             << " Successes=" << success_cnt
             << endl;
        sleep(5);
    }

    curl_global_cleanup();
    return 0;
}