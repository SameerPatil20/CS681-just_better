#ifndef REQUEST_H
#define REQUEST_H

#include <string>
#include <iomanip>
#include <sstream>

struct ThreadWorker;

/*
Class to store info about the received job, with methods to get response time
*/
struct Request {
    int id;
    int user_id;
    double arrival_time;
    double start_time = -1.0;
    double completion_time = -1.0;
    double service_total;
    double service_remaining;
    double timeout_deadline;
    bool timed_out = false;
    int retry_left;
    ThreadWorker* assigned_thread = nullptr;
    Request(int id_,int uid,double arr,double service,double timeout,int retry)
        : id(id_),user_id(uid),arrival_time(arr),service_total(service),service_remaining(service),timeout_deadline(arr + timeout),retry_left(retry) {}
    void mark_started(double t){
        if(start_time<0)start_time = t;
    }
    void mark_completed(double t){
        completion_time = t; service_remaining = 0.0;
    }
    double response_time()const{
        if (completion_time < 0) return -1.0;
        return completion_time - arrival_time;
    }
};

#endif