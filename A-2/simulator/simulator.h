#ifndef SIMULATOR_H
#define SIMULATOR_H

#include <queue>
#include <vector>
#include <memory>
#include <random>
#include <fstream>
#include "event.h"
#include "request.h"
#include "queueing_system.h"
#include "core.h"
using namespace std;

struct Result {
        double avg_response_time=-1.0;
        double throughput=0.0;
        double goodput=0.0;
        double badput=0.0;
        double util=0.0;
        int completed=0;
        int timedout=0;
        int dropped=0;
};

struct Simulator {
    double now=0.0;
    priority_queue<unique_ptr<Event>, vector<unique_ptr<Event>>, EventCompare> evq;
    QueueingSystem qsys;
    vector<Core*> cores;
    vector<Request*> all_requests;
    vector<Request*> completed_requests;
    vector<Request*> timedout_requests;
    int dropped_requests=0;
    int next_req_id=1;
    mt19937 rng;
    vector<string> trace_lines;
    int run_id=0;
    Simulator();
    ~Simulator();
    void push_event(unique_ptr<Event> e);
    unique_ptr<Event> pop_event();
    void make_cores(int ncores);
    void reset_for_run(unsigned seed);
    void schedule_initial_users(int num_users);
    void handle_user_arrival(int user_id);
    void handle_thread_slice_start(ThreadWorker* th, Core* core, double time);
    void handle_thread_slice_end(ThreadWorker* th, Core* core, double slice_len, double time);
    void handle_request_complete(Request* req, double time);
    void handle_request_timeout(Request* req, double time);
    void handle_thread_available(ThreadWorker* th, Core* core, double time);
    void release_thread_to_pool(ThreadWorker* th, double now);
    
    Result run(double simtime, double warmup_time, unsigned seed, int runid, bool trace_on);
    void write_trace(int runid);
};

#endif