#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>
#include "simulator.h"
#include "common.h"
#include <getopt.h>

int Event::seq_counter=0;

void usage() {
    std::cout <<
    "Usage: websim [OPTIONS]\n"
    "  --users N\n"
    "  --simtime T\n"
    "  --warmup W\n"
    "  --trace_on 0/1\n"
    "  --num_cores N\n"
    "  --max_threads N\n"
    "  --thread_queue_limit N\n"
    "  --quantum Q\n"
    "  --context_switch_overhead X\n"
    "  --think_base X\n"
    "  --think_mean_exp X\n"
    "  --closed_loop 0/1\n"
    "  --retry_limit N\n"
    "  --service_time_avg X\n"
    "  --timeout_lower X\n"
    "  --timeout_upper X\n"
    "  --rng_seed N\n"
    "  --trace_prefix STR\n"
    " --service_time_dist STR\n"
    " --sched_policy STR\n"
    << std::endl;
}

inline common::scheduling_policy sched_policy_type(string s){
    if(s == "RR"){
        return common::scheduling_policy::RR;
    }
    else if(s == "SJF"){
        return common::scheduling_policy::SJF;
    }
    else{
        cout << "UNRESOLVABLE SCHEDULING POLICY MAN\n";
        exit(1);
    }
}

int main(int argc, char** argv) {
    // int replications = 1;
    double simtime = 800.0;
    // double warmup = common::WARMUP_TIME;
    // int users = common::NUM_USERS;
    // bool trace_on = common::TRACE_ON;

    static struct option long_options[] = {
        {"users", required_argument, 0, 1000},
        {"simtime", required_argument, 0, 1001},
        {"warmup", required_argument, 0, 1002},
        {"trace_on", required_argument, 0, 1003},

        {"num_cores", required_argument, 0, 1004},
        {"max_threads", required_argument, 0, 1005},
        {"thread_queue_limit", required_argument, 0, 1006},
        {"quantum", required_argument, 0, 1007},
        {"context_switch_overhead", required_argument, 0, 1008},
        {"think_base", required_argument, 0, 1009},
        {"think_mean_exp", required_argument, 0, 1010},
        {"retry_limit", required_argument, 0, 1011},
        {"closed_loop", required_argument, 0, 1012},
        {"rng_seed", required_argument, 0, 1013},
        {"trace_prefix", required_argument, 0, 1014},
        {"service_time_avg", required_argument, 0, 1015},
        {"timeout_lower", required_argument, 0, 1016},
        {"timeout_upper", required_argument, 0, 1017},
        {"service_time_dist", required_argument, 0, 1018},
        {"sched_policy", required_argument, 0, 1019},
        {0, 0, 0, 0}
    };

    int opt;
    while ((opt = getopt_long(argc, argv, "", long_options, nullptr)) != -1) {
        switch (opt) {
            case 1000: common::NUM_USERS = std::atoi(optarg); break;
            case 1001: simtime = std::atof(optarg); break;
            case 1002: common::WARMUP_TIME = std::atof(optarg); break;
            case 1003: common::TRACE_ON = std::atoi(optarg) != 0; break;

            case 1004: common::NUM_CORES = std::atoi(optarg); break;
            case 1005: common::MAX_THREADS = std::atoi(optarg); break;
            case 1006: common::THREAD_QUEUE_LIMIT = std::atoi(optarg); break;
            case 1007: common::QUANTUM = std::atof(optarg); break;
            case 1008: common::CONTEXT_SWITCH_OVERHEAD = std::atof(optarg); break;
            case 1009: common::THINK_BASE = std::atof(optarg); break;
            case 1010: common::THINK_MEAN_EXP = std::atof(optarg); break;
            case 1011: common::RETRY_LIMIT = std::atoi(optarg); break;
            case 1012: common::CLOSED_LOOP = std::atoi(optarg) != 0; break;
            case 1013: common::RNG_SEED = static_cast<unsigned>(std::stoul(optarg)); break;
            case 1014: common::TRACE_PREFIX = std::string(optarg); break;
            case 1015: common::SERVICE_TIME_AVG = std::atof(optarg); break;
            case 1016: common::TIMEOUT_LOWER = std::atof(optarg); break;
            case 1017: common::TIMEOUT_UPPER = std::atof(optarg); break;
            case 1018: common::SERVICE_TIME_DIST = std::string(optarg);break;
            case 1019: common::SCHED_POLICY = sched_policy_type(std::string(optarg));break;

            default:
                usage();
                return 1;
        }
    }
    common::TIMEOUT_DIST=common::sampler(common::distribution_type::UNIFORM, common::TIMEOUT_LOWER, common::TIMEOUT_UPPER);

    if(common::SERVICE_TIME_DIST=="exponential"){
        common::SERVICE_DIST=common::sampler(common::distribution_type::EXPONENTIAL, common::SERVICE_TIME_AVG);
    }
    else if(common::SERVICE_TIME_DIST=="uniform"){
        common::SERVICE_DIST=common::sampler(common::distribution_type::UNIFORM, 20, common::SERVICE_TIME_AVG);
    }
    else if(common::SERVICE_TIME_DIST=="constant"){
        common::SERVICE_DIST=common::sampler(common::distribution_type::CONSTANT, common::SERVICE_TIME_AVG-10, common::SERVICE_TIME_AVG+10);
    }
    else{
        cout << "service time dist me bt"<<endl;
        exit(1);
    }

    // common::NUM_USERS = users;
    // common::WARMUP_TIME = warmup;
    // common::TRACE_ON = trace_on;

    Simulator sim;
    sim.make_cores(common::NUM_CORES);

    std::vector<Result> results;
    // for (int r=0; r<replications; ++r) {
    unsigned seed = common::RNG_SEED + 619 + 100;
    auto res = sim.run(simtime, common::WARMUP_TIME, seed, 0, common::TRACE_ON);
    results.push_back(res);
    std::cout <<fixed<<setprecision(5)<< "ResponseTime=" << res.avg_response_time/1000.0
                << " Throughput=" << res.throughput*1000 << " goodput=" << res.goodput*1000
                << " badput=" << res.badput*1000 << " completed=" << res.completed
                << " timedout=" << res.timedout << " dropped=" << res.dropped << " Util="<<res.util<< "\n";
    // }

    std::vector<double> avgs;
    for (auto &x: results) if (x.avg_response_time > -0.5) avgs.push_back(x.avg_response_time);
    double mean = 0.0;
    if (!avgs.empty()) {
        for (double v: avgs) mean += v;
        mean /= avgs.size();
    }
    // std::cout << "Aggregate avg_response_time (mean over runs): " << mean << "\n";
    return 0;
}