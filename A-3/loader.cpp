// loadgenerator.cpp
// One experiment per invocation.
// Usage example:
//   ./loadgenerator \
//     --device-write 10mb \
//     --cpus 0.5 \
//     --memory 500m \
//     --arrival-rate 20 \
//     --size 100 \
//     --cpuLoad 350 \
//     --num-requests 5000 \
//     --workers 8 \
//     --csv loadtest.csv

#include <arpa/inet.h>
#include <netdb.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstring>
#include <deque>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <numeric>
#include <sstream>
#include <string>
#include <thread>
#include <vector>
int COUNTER=0;

using namespace std;
using Clock = chrono::steady_clock;

struct Params {
    string admin_host = "127.0.0.1";
    int admin_port = 8080;

    string server_host = "127.0.0.1";
    int server_port = 80;

    string device_write;
    string memory;
    double cpus = 1.0;
    int arrival_rate = 10;
    int size = 100;
    int cpuLoad = 350;
    int num_requests = 5000;
    int workers = 8;

    int warmup_seconds = 2;
    string csv_file = "loadtest.csv";
};

struct Result {
    double throughput_rps = 0.0;
    double avg_response_ms = 0.0;
    double p90_response_ms = 0.0;
    int completed = 0;
};

struct Task {
    Clock::time_point scheduled_time;
};

static bool http_get(const string& host, int port, const string& path, string* response = nullptr) {
    addrinfo hints{};
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    addrinfo* res = nullptr;
    string port_str = to_string(port);

    if (getaddrinfo(host.c_str(), port_str.c_str(), &hints, &res) != 0) {
        return false;
    }

    int sockfd = -1;
    for (addrinfo* p = res; p != nullptr; p = p->ai_next) {
        sockfd = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (sockfd < 0) continue;

        timeval tv{};
        tv.tv_sec = 20;
        tv.tv_usec = 0;
        setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
        // cout << "Trying to connect to " << host << ":" << port << "..."<<endl;
        if (connect(sockfd, p->ai_addr, p->ai_addrlen) == 0) {
            break;
        }
        // cout << "Failed to connect to " << host << ":" << port << ": " << strerror(errno) << endl;
        close(sockfd);
        sockfd = -1;
    }
    cout << "CONNECTED TO " << host << ":" << port << endl;
    cout << COUNTER++ << endl;
    freeaddrinfo(res);

    if (sockfd < 0) return false;
    cout << "HERE"<<endl;
    ostringstream req;
    req << "GET " << path << " HTTP/1.1\r\n"
        << "Host: " << host << "\r\n"
        << "Connection: close\r\n"
        << "\r\n";
    
    // print on console for debugging
    // cout << "Request:\n" << req.str() << endl;
    string req_str = req.str();
    const char* data = req_str.c_str();
    size_t left = req_str.size();

    while (left > 0) {
        ssize_t n = send(sockfd, data, left, 0);
        if (n <= 0) {
            close(sockfd);
            return false;
        }
        data += n;
        left -= static_cast<size_t>(n);
    }

    shutdown(sockfd, SHUT_WR);

    char buf[4096];
    string resp;
    while (true) {
        ssize_t n = recv(sockfd, buf, sizeof(buf), 0);
        if (n > 0) {
            if (response) resp.append(buf, buf + n);
            // cout.write(buf, n);
        } else {
            break;
        }
    }

    close(sockfd);
    if (response) *response = move(resp);
    return true;
}

class WorkQueue {
public:
    void push(Task t) {
        {
            lock_guard<mutex> lk(m_);
            q_.push_back(move(t));
        }
        cv_.notify_one();
    }

    bool pop(Task& out) {
        unique_lock<mutex> lk(m_);
        cv_.wait(lk, [&] { return done_ || !q_.empty(); });
        if (q_.empty()) return false;
        out = q_.front();
        q_.pop_front();
        return true;
    }

    void set_done() {
        {
            lock_guard<mutex> lk(m_);
            done_ = true;
        }
        cv_.notify_all();
    }
    deque<Task> q_;
    mutex m_;
    condition_variable cv_;
    bool done_ = false;
};

static string make_workload_path(int size, int cpuLoad) {
    ostringstream os;
    os << "/server.php?size=" << size << "&cpuLoad=" << cpuLoad;
    return os.str();
}

static string make_start_path(const Params& p) {
    ostringstream os;
    os << "/dockerStart.php?memory=" << p.memory
       << "&cpus=" << p.cpus
       << "&device-write=" << p.device_write;
    return os.str();
}

static string make_stop_path() {
    return "/dockerStop.php";
}

static Result run_test(const string& server_host,
                       int server_port,
                       const string& workload_path,
                       int arrival_rate,
                       int num_requests,
                       int workers) {
    WorkQueue queue;
    mutex lat_m;
    vector<double> latencies_ms;
    latencies_ms.reserve(num_requests);

    atomic<int> completed{0};

    auto worker_fn = [&]() {
        Task task;
        while (queue.pop(task)) {
            auto t0 = task.scheduled_time;
            string resp;
            bool ok = http_get(server_host, server_port, workload_path, &resp);
            (void)ok;
            auto t1 = Clock::now();
            double rt_ms = chrono::duration<double, milli>(t1 - t0).count();
            {
                lock_guard<mutex> lk(lat_m);
                latencies_ms.push_back(rt_ms);
            }
            completed.fetch_add(1, memory_order_relaxed);
        }
    };

    vector<thread> pool;
    for (int i = 0; i < workers; ++i) {
        pool.emplace_back(worker_fn);
    }

    auto start = Clock::now();
    double interval_sec = 1.0 / max(1, arrival_rate);

    for (int i = 0; i < num_requests; ++i) {
        auto scheduled = start + chrono::duration_cast<Clock::duration>(
            chrono::duration<double>(i * interval_sec));
        this_thread::sleep_until(scheduled);
        queue.push(Task{scheduled});
    }

    queue.set_done();
    for (auto& th : pool) th.join();
    auto end = Clock::now();

    Result stats;
    stats.completed = completed.load(memory_order_relaxed);

    double elapsed_s = chrono::duration<double>(end - start).count();
    stats.throughput_rps = (elapsed_s > 0.0) ? (stats.completed / elapsed_s) : 0.0;

    if (!latencies_ms.empty()) {
        double sum = accumulate(latencies_ms.begin(), latencies_ms.end(), 0.0);
        stats.avg_response_ms = sum / latencies_ms.size();

        sort(latencies_ms.begin(), latencies_ms.end());
        size_t idx90 = static_cast<size_t>(0.90 * (latencies_ms.size() - 1));
        stats.p90_response_ms = latencies_ms[idx90];
    }

    return stats;
}

static bool parse_int(const string& s, int& out) {
    try {
        size_t pos = 0;
        int v = stoi(s, &pos);
        if (pos != s.size()) return false;
        out = v;
        return true;
    } catch (...) {
        return false;
    }
}

static bool parse_double(const string& s, double& out) {
    try {
        size_t pos = 0;
        double v = stod(s, &pos);
        if (pos != s.size()) return false;
        out = v;
        return true;
    } catch (...) {
        return false;
    }
}

static void usage(const char* prog) {
    cerr <<
    "Usage:\n"
    "  " << prog << " --device-write 10mb --cpus 0.5 --memory 500m --arrival-rate 20\n"
    "       --size 100 --cpuLoad 350 --num-requests 5000 --workers 8 --csv loadtest.csv\n\n"
    "Optional:\n"
    "  --admin-host 127.0.0.1 --admin-port 8080 --server-host 127.0.0.1 --server-port 80 --warmup 2\n";
}

int param_setter(int argc, char* argv[], Params& p) {
    for (int i = 1; i < argc; ++i) {
        string arg = argv[i];

        auto need_value = [&](const string& name) -> string {
            if (i + 1 >= argc) {
                cerr << "Missing value for " << name << "\n";
                exit(1);
            }
            return argv[++i];
        };

        if (arg == "--device-write") {
            p.device_write = need_value(arg);
        } else if (arg == "--memory") {
            p.memory = need_value(arg);
        } else if (arg == "--cpus") {
            if (!parse_double(need_value(arg), p.cpus)) {
                cerr << "Invalid value for --cpus\n";
                return 1;
            }
        } else if (arg == "--arrival-rate") {
            if (!parse_int(need_value(arg), p.arrival_rate)) {
                cerr << "Invalid value for --arrival-rate:" << argv[i] << "\n";
                return 1;
            }
        } else if (arg == "--size") {
            if (!parse_int(need_value(arg), p.size)) {
                cerr << "Invalid value for --size\n";
                return 1;
            }
        } else if (arg == "--cpuLoad") {
            if (!parse_int(need_value(arg), p.cpuLoad)) {
                cerr << "Invalid value for --cpuLoad\n";
                return 1;
            }
        } else if (arg == "--num-requests") {
            if (!parse_int(need_value(arg), p.num_requests)) {
                cerr << "Invalid value for --num-requests\n";
                return 1;
            }
        } else if (arg == "--workers") {
            if (!parse_int(need_value(arg), p.workers)) {
                cerr << "Invalid value for --workers\n";
                return 1;
            }
        } else if (arg == "--csv") {
            p.csv_file = need_value(arg);
        } else if (arg == "--admin-host") {
            p.admin_host = need_value(arg);
        } else if (arg == "--admin-port") {
            if (!parse_int(need_value(arg), p.admin_port)) {
                cerr << "Invalid value for --admin-port\n";
                return 1;
            }
        } else if (arg == "--server-host") {
            p.server_host = need_value(arg);
        } else if (arg == "--server-port") {
            if (!parse_int(need_value(arg), p.server_port)) {
                cerr << "Invalid value for --server-port\n";
                return 1;
            }
        } else if (arg == "--warmup") {
            if (!parse_int(need_value(arg), p.warmup_seconds)) {
                cerr << "Invalid value for --warmup\n";
                return 1;
            }
        } else if (arg == "--help") {
            usage(argv[0]);
            return 0;
        } else {
            cerr << "Unknown argument: " << arg << "\n";
            usage(argv[0]);
            return 1;
        }
    }
    return 0;
}

int main(int argc, char* argv[]) {

    Params p;
    if (param_setter(argc, argv, p)!=0){
        return 1;
    }

    string start_path = make_start_path(p);
    string stop_path = make_stop_path();
    string workload_path = make_workload_path(p.size, p.cpuLoad);

    bool write_header = false;
    {
        ifstream in(p.csv_file);
        write_header = !in.good() || in.peek() == ifstream::traits_type::eof();
    }

    ofstream csv(p.csv_file, ios::app);
    cout << "Starting container: "
         << "device_write=" << p.device_write
         << ", cpu=" << p.cpus
         << ", mem=" << p.memory
         << ", arr=" << p.arrival_rate
         << ", size=" << p.size
         << ", cpuLoad=" << p.cpuLoad
         << endl;

    // if (!http_get(p.admin_host, p.admin_port, start_path)) {
    //     cerr << "Failed to start container.\n";
    //     return 1;
    // }

    this_thread::sleep_for(chrono::seconds(p.warmup_seconds));

    Result stats = run_test(p.server_host, p.server_port, workload_path,
                            p.arrival_rate, p.num_requests, p.workers);

    // if (!http_get(p.admin_host, p.admin_port, stop_path)) {
    //     cerr << "Warning: failed to stop container cleanly.\n";
    // }
    csv << p.arrival_rate << ","
        << p.device_write << ","
        << p.cpus << ","
        << p.memory << ","
        << p.cpuLoad << ","
        << fixed << setprecision(4)
        << stats.throughput_rps << ","
        << stats.avg_response_ms << ","
        << stats.p90_response_ms << ","
        << stats.completed << "\n";

    csv.flush();

    cout << "Done: throughput=" << stats.throughput_rps
         << " rps, avgRT=" << stats.avg_response_ms
         << " ms, p90RT=" << stats.p90_response_ms
         << " ms, completed=" << stats.completed
         << endl;

    return 0;
}