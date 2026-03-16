#ifndef CORE_H
#define CORE_H

#include <deque>
#include <vector>
#include "event.h"

struct Simulator;

struct Core {
    int core_id;
    double quantum;
    double ctx_overhead;
    Simulator* sim = nullptr;
    std::deque<ThreadWorker*> runqueue;
    ThreadWorker* current_thread = nullptr;
    bool idle = true;
    Core(int id=0, double q=5.0, double o=0.1, Simulator* s=nullptr) : core_id(id), quantum(q), ctx_overhead(o), sim(s) {}
    void add_runnable(ThreadWorker* th);
    void schedule_next_slice(double now);
    void handle_slice_start(double now, ThreadWorker* th);
    void handle_slice_end(double now, ThreadWorker* th, double slice_len);
};

#endif