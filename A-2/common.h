// #ifndef COMMON_H
// #define COMMON_H

// #include <random>
// #include <string>
// #include <tuple>
// using namespace std;

// namespace common{
//     inline int NUM_CORES=8;
//     inline int MAX_THREADS=256;
//     inline int THREAD_QUEUE_LIMIT=10000;
//     inline double QUANTUM=10.0;
//     inline double CONTEXT_SWITCH_OVERHEAD=0.1;
//     inline int NUM_USERS=50;//baadme set hoga
//     inline double THINK_BASE=3000.0;
//     inline double THINK_MEAN_EXP=200.0;
//     inline int RETRY_LIMIT=1;
//     inline bool CLOSED_LOOP=true;
//     inline double WARMUP_TIME=1000.0;//baadme set hoga
//     inline unsigned RNG_SEED=619;
//     inline bool TRACE_ON=true;//baadme set hoga
//     inline std::string TRACE_PREFIX="runs/run";

//     enum class distribution_type{
//         CONSTANT, 
//         UNIFORM, 
//         EXPONENTIAL,
//         NORMAL 
//     };
//     struct sampler {
//         distribution_type type;
//         double p1;
//         double p2;
//         sampler(distribution_type t=distribution_type::EXPONENTIAL, double a=300.0, double b=0.0){
//             p1=a;
//             p2=b;
//             type=t;
//         }
//     };
//     inline double sample_dist(std::mt19937 &rng, const sampler &d) {
//         switch (d.type) {
//             case distribution_type::CONSTANT: return d.p1;
//             case distribution_type::UNIFORM: {
//                 uniform_real_distribution<double> dist(d.p1, d.p2);
//                 return dist(rng);
//             }
//             case distribution_type::EXPONENTIAL: {
//                 // p1 is mean
//                 exponential_distribution<double> dist(1.0 / d.p1);
//                 return dist(rng);
//             }
//             case distribution_type::NORMAL: {
//                 normal_distribution<double> dist(d.p1, d.p2);
//                 double x=dist(rng);
//                 return std::abs(x);
//             }
//         }
//         return d.p1;
//     }

//     inline sampler SERVICE_DIST=sampler(distribution_type::EXPONENTIAL, 50.0);
//     inline sampler TIMEOUT_DIST=sampler(distribution_type::UNIFORM, 5000, 10000);
// }

// #endif

#ifndef COMMON_H
#define COMMON_H

#include <random>
#include <string>
#include <tuple>
using namespace std;

namespace common{
    enum class scheduling_policy{
        FCFS,
        SJF
    };
    inline int NUM_CORES=1;
    inline int MAX_THREADS=346;
    inline int THREAD_QUEUE_LIMIT=10000;
    inline double QUANTUM=10.0;
    inline double CONTEXT_SWITCH_OVERHEAD=0.2;
    inline int NUM_USERS=50;//baadme set hoga
    inline double THINK_BASE=4000.0;
    inline double THINK_MEAN_EXP=10.0;
    inline int RETRY_LIMIT=0;
    inline bool CLOSED_LOOP=true;
    inline double WARMUP_TIME=100000.0;//baadme set hoga
    inline unsigned RNG_SEED=6190;
    inline bool TRACE_ON=true;//baadme set hoga
    inline std::string TRACE_PREFIX="runs/run";
    inline double SERVICE_TIME_AVG=30.0;
    inline double TIMEOUT_LOWER = 3000;
    inline double TIMEOUT_UPPER = 3001;
    inline string SERVICE_TIME_DIST = "exponential";
    inline scheduling_policy SCHED_POLICY = scheduling_policy::FCFS;


    enum class distribution_type{
        CONSTANT, 
        UNIFORM, 
        EXPONENTIAL,
        NORMAL 
    };
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
                uniform_real_distribution<double> dist(d.p1, d.p2);
                return dist(rng);
            }
            case distribution_type::EXPONENTIAL: {
                // p1 is mean
                exponential_distribution<double> dist(1.0 / d.p1);
                return dist(rng);
            }
            case distribution_type::NORMAL: {
                normal_distribution<double> dist(d.p1, d.p2);
                double x=dist(rng);
                return std::abs(x);
            }
        }
        return d.p1;
    }

    inline sampler SERVICE_DIST=sampler(distribution_type::EXPONENTIAL, SERVICE_TIME_AVG);
    inline sampler TIMEOUT_DIST=sampler(distribution_type::UNIFORM, TIMEOUT_LOWER, TIMEOUT_UPPER);
}

#endif