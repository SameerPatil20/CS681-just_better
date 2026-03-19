#ifndef THREADWORKER_H
#define THREADWORKER_H
#include "request.h"

struct Core;
struct Request;

/*
Class corresponding to each thread. These hold a job, and get scheduled on their 
corresponding core
*/
struct ThreadWorker {
    int tid;
    Core* core;
    Request* req=nullptr;
    bool busy=false;
    ThreadWorker(int id=0, Core* c=nullptr): tid(id), core(c) {}
    void assign_request(Request* r){
        req=r;
        busy=true;
        if(req)req->assigned_thread=this;
    }
    Request* release(){
        Request* r=req;
        if(r)r->assigned_thread=nullptr;
        req=nullptr;
        busy=false;
        return r;
    }
    bool is_busy(){
        return busy;
    }
};

#endif