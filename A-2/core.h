#ifndef CORE_H
#define CORE_H

#include <deque>
#include <vector>
// #include <
#include "event.h"
#include "common.h"
#include "threadworker.h"
struct Simulator;

struct SJF_comparator{
    bool operator()(const ThreadWorker* a, const ThreadWorker* b) const {
        if(!a->req || !b->req){
            return false;
        }
        return a->req->service_remaining > b->req->service_remaining; 
    }
};

struct Core {
    private:
        std::deque<ThreadWorker*> runqueue;
        std::priority_queue<ThreadWorker*,vector<ThreadWorker*>, SJF_comparator> runpriorityqueue;
    public:
        int core_id;
        double quantum;
        double ctx_overhead;
        double busy_time;
        Simulator* sim = nullptr;
        common::scheduling_policy sched_policy;
        ThreadWorker* current_thread = nullptr;
        bool idle = true;
        Core(int id=0, double q=5.0, double o=0.1, Simulator* s=nullptr) : core_id(id), quantum(q), ctx_overhead(o), sim(s) {
            busy_time=0.0;
            sched_policy = common::SCHED_POLICY;
        }
        void add_runnable(ThreadWorker* th);
        void schedule_next_slice(double now);
        void handle_slice_start(double now, ThreadWorker* th);
        void handle_slice_end(double now, ThreadWorker* th, double slice_len);
        void add_thread(ThreadWorker* th);
        bool is_empty();
        ThreadWorker* pop_one();
    // {
        // runqueue.push_back(th);
        // runpriorityqueue.push(th);
    // }
    // void 
};

#endif