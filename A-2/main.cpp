#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>
#include "simulator.h"
#include "common.h"
#include <getopt.h>

int Event::seq_counter=0;

void usage() {
    std::cout << "Usage: websim [--users U] [--simtime T] [--warmup W] [--trace_on 0/1]\n";
}

int main(int argc, char** argv) {
    // int replications = 1;
    double simtime = 800.0;
    double warmup = common::WARMUP_TIME;
    int users = common::NUM_USERS;
    bool trace_on = common::TRACE_ON;

    static struct option long_options[] = {
        {"users", required_argument, 0, 'u'},
        {"simtime", required_argument, 0, 's'},
        {"warmup", required_argument, 0, 'w'},
        {"trace_on", required_argument, 0, 't'},
        {0,0,0,0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "u:s:w:t:", long_options, nullptr)) != -1) {
        switch (opt) {
            case 'u': users = std::atoi(optarg); break;
            case 's': simtime = std::atof(optarg); break;
            case 'w': warmup = std::atof(optarg); break;
            case 't': trace_on = std::atoi(optarg) != 0; break;
            default: usage(); return 1;
        }
    }

    common::NUM_USERS = users;
    common::WARMUP_TIME = warmup;
    common::TRACE_ON = trace_on;

    Simulator sim;
    sim.make_cores(common::NUM_CORES);

    std::vector<Result> results;
    // for (int r=0; r<replications; ++r) {
    unsigned seed = common::RNG_SEED + 9 + 100;
    auto res = sim.run(simtime, warmup, seed, 0, trace_on);
    results.push_back(res);
    std::cout <<fixed<<setprecision(5)<< "RUN: avg_rt=" << res.avg_response_time
                << " throughput=" << res.throughput << " goodput=" << res.goodput
                << " badput=" << res.badput << " completed=" << res.completed
                << " timedout=" << res.timedout << " dropped=" << res.dropped << "\n";
    // }

    std::vector<double> avgs;
    for (auto &x: results) if (x.avg_response_time > -0.5) avgs.push_back(x.avg_response_time);
    double mean = 0.0;
    if (!avgs.empty()) {
        for (double v: avgs) mean += v;
        mean /= avgs.size();
    }
    std::cout << "Aggregate avg_response_time (mean over runs): " << mean << "\n";
    return 0;
}