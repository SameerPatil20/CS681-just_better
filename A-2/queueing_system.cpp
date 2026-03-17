#include "queueing_system.h"
#include "simulator.h"
#include "common.h"
#include <cassert>

void QueueingSystem::set_cores(const std::vector<Core*>& cs) {
    cores = cs;
    threads.clear();
    free_threads.clear();
    int nc = (int)cores.size();
    for (int t=0; t<common::MAX_THREADS; ++t) {
        Core* c = cores[t % nc];
        ThreadWorker* th = new ThreadWorker(t, c);
        threads.push_back(th);
        free_threads.push_back(th);
    }
}

bool QueueingSystem::admit_request(Request* req, double now) {
    if (!free_threads.empty()) {
        ThreadWorker* th = free_threads.front();
        free_threads.pop_front();
        th->assign_request(req);
        th->core->add_runnable(th);
        return true;
    } 
    else {
        if ((int)waiting_requests.size() < common::THREAD_QUEUE_LIMIT) {
            waiting_requests.push_back(req);
            return true;
        } 
        else {
            return false;
        }
    }
}

void QueueingSystem::release_thread_to_pool(ThreadWorker* th, double now) {
    if (!waiting_requests.empty()) {
        Request* r = waiting_requests.front();
        waiting_requests.pop_front();
        th->assign_request(r);
        th->core->add_runnable(th);
    } else {
        free_threads.push_back(th);
    }
}