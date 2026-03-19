#ifndef EVENT_H
#define EVENT_H

#include <cstdint>
#include <atomic>
#include <memory>

struct Request;
struct ThreadWorker;
struct Core;

/*
defines the various types of events
*/
enum class event_type{
    USER_ARRIVAL,
    THREAD_SLICE_START,
    THREAD_SLICE_END,
    REQUEST_COMPLETE,
    REQUEST_TIMEOUT,
    THREAD_AVAILABLE,
    CHECK_TIMEOUT,
};

struct Event {
    double time;
    event_type type;
    Request* req = nullptr;
    ThreadWorker* thread = nullptr;
    Core* core = nullptr;
    double slice_len = 0.0;
    int user_id = -1;
    int req_id=-1;

    uint64_t seq;

    Event(double t, event_type ty) : time(t), type(ty), seq(++seq_counter) {}
    Event(double t, event_type ty, Request* r) : Event(t,ty) {
        req = r; 
    }
    Event(double t, event_type ty, ThreadWorker* th, Core* c) : Event(t,ty){
        thread = th; 
        core = c;
    }
    Event(double t, event_type ty, ThreadWorker* th, Core* c, double sl) : Event(t,ty,th,c){ 
        slice_len = sl; 
    }
    Event(double t, event_type ty, int uid) : Event(t,ty) { user_id = uid; }
    static int seq_counter;
    // Event(double t, event_type ty, ThreadWorker* th, Core* c, int req_id) : Event(t,ty,th,c){
    //     req_id = req_id;
    // }
};

/*
this is to sort the events by start time
*/
struct EventCompare {
    bool operator()(const std::unique_ptr<Event>& a, const std::unique_ptr<Event>& b) const {
        if (a->time != b->time) return a->time > b->time;
        return a->seq > b->seq;
    }
};

#endif