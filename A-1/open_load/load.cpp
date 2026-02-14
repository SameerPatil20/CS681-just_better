#include <curl/curl.h>
#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <mutex>
#include <random>
#include <algorithm>
#include <numeric>

using namespace std;
using namespace chrono;

const string URL = "http://10.61.1.109/test.php";
const int DURATION = 180;     
const int MAX_CONCURRENCY = 10000;

atomic<int> completed(0);
atomic<int> failed(0);
vector<double> latencies;
mutex lat_mtx;

size_t discard(void *ptr, size_t size, size_t nmemb, void *userdata) {
    return size * nmemb;
}

void send_request() {
    CURL *curl = curl_easy_init();
    if (!curl) {
        failed++;
        return;
    }

    curl_easy_setopt(curl, CURLOPT_URL, URL.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, discard);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);

    auto start = steady_clock::now();
    CURLcode res = curl_easy_perform(curl);
    auto end = steady_clock::now();

    double latency = duration<double>(end - start).count();

    if (res == CURLE_OK) {
        completed++;
        lock_guard<mutex> lock(lat_mtx);
        latencies.push_back(latency);
    } else {
        failed++;
    }

    curl_easy_cleanup(curl);
}

int main() {
    curl_global_init(CURL_GLOBAL_ALL);

    random_device rd;
    mt19937 gen(rd());

    for (int RATE = 10; RATE < 400; RATE += 4) {
        this_thread::sleep_for(seconds(1));

        completed = 0;
        failed = 0;
        latencies.clear();

        exponential_distribution<double> exp_dist(RATE);

        auto exp_start = steady_clock::now();

        while (duration_cast<seconds>(steady_clock::now() - exp_start).count() < DURATION) {
            thread(send_request).detach();

            double sleep_time = exp_dist(gen);
            this_thread::sleep_for(duration<double>(sleep_time));
        }

        this_thread::sleep_for(seconds(10));

        double exp_time = DURATION;

        int comp = completed.load();
        int fail = failed.load();
        double throughput = comp / exp_time;

        cout << "====== RESULTS ======\n";
        cout << "rate:" << RATE << "\n";
        cout << "Duration           : " << exp_time << " s\n";
        cout << "Completed requests : " << comp << "\n";
        cout << "Failed requests    : " << fail << "\n";
        cout << "Throughput         : " << throughput << " req/s\n";

        if (!latencies.empty()) {
            sort(latencies.begin(), latencies.end());
            double avg = accumulate(latencies.begin(), latencies.end(), 0.0) / latencies.size();
            double p95 = latencies[(int)(0.95 * latencies.size())];
            double mx = latencies.back();

            cout << "Avg latency        : " << avg << " s\n";
            cout << "P95 latency        : " << p95 << " s\n";
            cout << "Max latency        : " << mx << " s\n";
        }

        this_thread::sleep_for(seconds(20));
    }

    curl_global_cleanup();
    return 0;
}
