#ifndef QUEUEING_SYSTEM_H
#define QUEUEING_SYSTEM_H

#include <deque>
#include <vector>
#include "request.h"
#include "threadworker.h"
#include "core.h"

using namespace std;

struct Simulator;

struct QueueingSystem {
    Simulator* sim = nullptr;
    vector<Core*> cores;
    vector<ThreadWorker*> threads;
    deque<ThreadWorker*> free_threads;
    deque<Request*> waiting_requests;

    QueueingSystem(Simulator* s=nullptr) : sim(s) {}

    void set_cores(const std::vector<Core*>& cs);
    bool admit_request(Request* req, double now);
    void release_thread_to_pool(ThreadWorker* th, double now);
};

#endif