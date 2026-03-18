#include "core.h"
#include "simulator.h"
#include "event.h"
#include "common.h"
#include <memory>
#include<iostream>



void Core::add_runnable(ThreadWorker* th) {
    runqueue.push_back(th);
    runpriorityqueue.push(th);
    if (idle) schedule_next_slice(sim->now);
}

void Core::add_thread(ThreadWorker* th){
    runqueue.push_back(th);
    runpriorityqueue.push(th);
}
bool Core::is_empty(){
    if(sched_policy == common::scheduling_policy::RR){
        return runqueue.empty();
    }
    else if(sched_policy == common::scheduling_policy::SJF){
        return runpriorityqueue.empty();
    }
    else return true;
}

ThreadWorker* Core::pop_one(){
    if(is_empty()){
        cout<<"POP ON EMPTY CORE ID: "<< core_id<<endl;
        exit(1);
    }
    else{
        ThreadWorker* ret;
        if(sched_policy == common::scheduling_policy::RR){
            ret = runqueue.front();
            runqueue.pop_front();
            return ret;
        }
        else if(sched_policy == common::scheduling_policy::SJF){
            ret = runpriorityqueue.top();
            runpriorityqueue.pop();
            return ret;
        }
        else{
            cout << "YE KONSI POLICY HAI BHAI?\n";
            exit(1);
        }
    }
}

void Core::schedule_next_slice(double now) {
    if (is_empty()) { idle = true; current_thread = nullptr; return; }
    ThreadWorker* th = pop_one();
    current_thread = th;
    idle = false;
    auto ev = std::make_unique<Event>(now, event_type::THREAD_SLICE_START, th, this);
    sim->push_event(std::move(ev));
}

void Core::handle_slice_start(double now, ThreadWorker* th) {
    Request* r = th->req;
    if (!r) {
        schedule_next_slice(now);
        return;
    }
    // std::cout<<"thread id: "<<th->tid<<" is now being RUN, time = "<<now<<" being push back into cor id: "<< core_id<<" with time left = "<<r->service_remaining<<std::endl;
    r->mark_started(now);
    double slice_len = std::min(quantum, r->service_remaining);
    // busy_time += slice_len;
    auto ev = std::make_unique<Event>(now + slice_len, event_type::THREAD_SLICE_END, th, this, slice_len);

    sim->push_event(std::move(ev));
}

void Core::handle_slice_end(double now, ThreadWorker* th, double slice_len) {
    Request* r = th->req;
    if (!r) { schedule_next_slice(now); return; }
    r->service_remaining -= slice_len;
    // busy_time += slice_len + common::CONTEXT_SWITCH_OVERHEAD;
    if (r->service_remaining <= 1e-7) {
        // cout <<"thread: "<<th->tid<<" complete"<<endl;
        r->mark_completed(now);
        auto ev = std::make_unique<Event>(now, event_type::REQUEST_COMPLETE, r);
        sim->push_event(std::move(ev));
        th->release();
        sim->release_thread_to_pool(th, now);
        schedule_next_slice(now);
    } 
    else {
        double t_avail = now+ctx_overhead;
        // std::cout<<"thread id: "<<th->tid<<" is now being removed from run, time = "<<now<<", being push back into cor id: "<< core_id<<" with time left = "<<r->service_remaining<<std::endl;

        auto ev = std::make_unique<Event>(t_avail, event_type::THREAD_AVAILABLE, th, this);
        sim->push_event(std::move(ev));
        idle = true; current_thread = nullptr;
        // schedule_next_slice(now+common::CONTEXT_SWITCH_OVERHEAD);
    }
}