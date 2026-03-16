#ifndef COMMON_H
#define COMMON_H

#include <random>
#include <string>
#include <tuple>

namespace common{
    inline int NUM_CORES=4;
    inline int MAX_THREADS=32;
    inline int THREAD_QUEUE_LIMIT=300;
    inline double QUANTUM=20.0;
    inline double CONTEXT_SWITCH_OVERHEAD=0.1;
    inline int NUM_USERS=50;
    inline double THINK_BASE=100.0;
    inline double THINK_MEAN_EXP=200.0;
    inline int RETRY_LIMIT=1;
    inline bool CLOSED_LOOP=true;
    inline double WARMUP_TIME=1000.0;
    inline unsigned RNG_SEED=619;
    inline bool TRACE_ON=true;
    inline std::string TRACE_PREFIX="runs/run";

    enum class distribution_type { CONSTANT, UNIFORM, EXPONENTIAL, NORMAL };

    struct sampler {
        distribution_type type;
        double p1;
        double p2;
        sampler(distribution_type t=distribution_type::EXPONENTIAL, double a=300.0, double b=0.0){
            p1=a;
            p2=b;
            type=t;
        }
    };


    inline double sample_dist(std::mt19937 &rng, const sampler &d) {
        switch (d.type) {
            case distribution_type::CONSTANT: return d.p1;
            case distribution_type::UNIFORM: {
                std::uniform_real_distribution<double> dist(d.p1, d.p2);
                return dist(rng);
            }
            case distribution_type::EXPONENTIAL: {
                // p1 is mean
                std::exponential_distribution<double> dist(1.0 / d.p1);
                return dist(rng);
            }
            case distribution_type::NORMAL: {
                std::normal_distribution<double> dist(d.p1, d.p2);
                double x=dist(rng);
                return std::abs(x);
            }
        }
        return d.p1;
    }

    inline sampler SERVICE_DIST=sampler(distribution_type::EXPONENTIAL, 30.0);
    inline sampler TIMEOUT_DIST=sampler(distribution_type::UNIFORM, 100.0, 300.0);
}

#endif