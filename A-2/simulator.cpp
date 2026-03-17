#include "simulator.h"
#include "common.h"
#include <iostream>
#include <sstream>
#include <cmath>
#include <iomanip>
#include <filesystem>

using namespace std;

Simulator::Simulator() : qsys(this),rng(common::RNG_SEED) {}

Simulator::~Simulator() {
    for (auto r : all_requests) delete r;
    for (auto th : qsys.threads) delete th;
    for (auto c : cores) delete c;
}

void Simulator::push_event(unique_ptr<Event> e) {
    evq.push(std::move(e));
}

unique_ptr<Event> Simulator::pop_event() {
    if (evq.empty()) return nullptr;
    auto e = std::move(const_cast<unique_ptr<Event>&>(evq.top()));
    evq.pop();
    return e;
}

void Simulator::make_cores(int ncores) {
    for (auto c : cores) delete c;
    cores.clear();
    for (int i=0;i<ncores;++i) {
        Core* c = new Core(i,common::QUANTUM,common::CONTEXT_SWITCH_OVERHEAD,this);
        cores.push_back(c);
    }
}

void Simulator::reset_for_run(unsigned seed) {
    now = 0.0;
    while (!evq.empty()) evq.pop();
    for (auto r : all_requests) { delete r; } all_requests.clear();
    completed_requests.clear();
    timedout_requests.clear();
    dropped_requests = 0;
    next_req_id = 1;
    trace_lines.clear();
    rng.seed(seed);
}

void Simulator::schedule_initial_users(int num_users) {
    exponential_distribution<double> expdist(1.0 / common::THINK_MEAN_EXP);
    uniform_real_distribution<double> stagger(0.1,5000);
    for (int uid=0; uid<num_users; ++uid) {
        double start = common::THINK_BASE + expdist(rng) + stagger(rng);
        auto ev = make_unique<Event>(start,event_type::USER_ARRIVAL,uid);
        push_event(std::move(ev));
    }
}

void Simulator::handle_user_arrival(int user_id) {
    double nowt = now;
    double service = common::sample_dist(rng,common::SERVICE_DIST);
    double timeout = common::sample_dist(rng,common::TIMEOUT_DIST);
    int rid = next_req_id++;
    Request* req = new Request(rid,user_id,nowt,service,timeout,common::RETRY_LIMIT);
    all_requests.push_back(req);
    bool admitted = qsys.admit_request(req,nowt);
    if (!admitted) {
        ++dropped_requests;
        exponential_distribution<double> expdist(1.0 / common::THINK_MEAN_EXP);
        double think = common::THINK_BASE + expdist(rng);
        double next_t = now + think;
        auto ev = make_unique<Event>(next_t,event_type::USER_ARRIVAL,req->user_id);
        push_event(std::move(ev));
        if (common::TRACE_ON) {
            ostringstream ss;
            ss << "DROP," << fixed << setprecision(3) << nowt << "," << req->id << "," << user_id;
            trace_lines.push_back(ss.str());
        }
    } 
    else {
        if (common::TRACE_ON) {
            ostringstream ss;
            ss << "ARRIVAL," << fixed << setprecision(3) << nowt << "," << req->id << "," << user_id << "," << service << "," << timeout;
            trace_lines.push_back(ss.str());
        }
    }
}

void Simulator::handle_thread_slice_start(ThreadWorker* th,Core* core,double time) {
    core->handle_slice_start(time,th);
}

void Simulator::handle_thread_slice_end(ThreadWorker* th,Core* core,double slice_len,double time) {
    if(time >= common::WARMUP_TIME){
        core->busy_time += slice_len;
    }
    core->handle_slice_end(time,th,slice_len);
}

void Simulator::handle_thread_available(ThreadWorker* th,Core* core,double time) {
    // cout<<"thread id: "<<th->tid<<" is now available,at time "<<time<<",being push back into cor id: "<< core->core_id<<endl;
    core->runqueue.push_back(th);
    if (core->idle) core->schedule_next_slice(time);
}

void Simulator::handle_request_complete(Request* req,double time) {
    if(req->timeout_deadline<= req->completion_time){
        //timeout hua hai,badput
        // cout <<req->timeout_deadline
        req->timed_out=true;
        timedout_requests.push_back(req);
        if(common::TRACE_ON){
            ostringstream ss;
            ss << "TIMEOUT," << fixed << setprecision(3) << time << "," << req->id << "," << req->user_id;
            trace_lines.push_back(ss.str());
        }
        // if (req->retry_left > 0) {
        //     req->retry_left -= 1;
        //     double backoff = 10.0;
        //     auto ev = make_unique<Event>(time + backoff,event_type::USER_ARRIVAL,req->user_id);
        //     push_event(std::move(ev));
        // }
    }
    else{
        completed_requests.push_back(req);
        if (common::TRACE_ON) {
            ostringstream ss;
            ss << "COMPLETE," << fixed << setprecision(3) << time << "," << req->id << "," << req->user_id << "," << req->response_time();
            trace_lines.push_back(ss.str());
        }
    }
    if (common::CLOSED_LOOP) {
        exponential_distribution<double> expdist(1.0 / common::THINK_MEAN_EXP);
        double think = common::THINK_BASE + expdist(rng);
        double next_t = time + think;
        auto ev = make_unique<Event>(next_t,event_type::USER_ARRIVAL,req->user_id);
        push_event(std::move(ev));
    }
    // completed_requests.push_back(req);
    // if (common::TRACE_ON) {
    //     ostringstream ss;
    //     ss << "COMPLETE," << fixed << setprecision(3) << time << "," << req->id << "," << req->user_id << "," << req->response_time();
    //     trace_lines.push_back(ss.str());
    // }
    // schedule closed-loop next arrival for this user
}

// void Simulator::handle_request_timeout(Request* req,double time) {
//     if (req->completion_time < 0.0) {
//         req->timed_out = true;
//         timedout_requests.push_back(req);
//         if (common::TRACE_ON) {
            // ostringstream ss;
            // ss << "TIMEOUT," << fixed << setprecision(3) << time << "," << req->id << "," << req->user_id;
            // trace_lines.push_back(ss.str());
//         }
//         // if assigned thread exists,release it
//         if (req->assigned_thread != nullptr) {
//             ThreadWorker* th = req->assigned_thread;
//             if (th->is_busy()) {
//                 th->release();
//                 release_thread_to_pool(th,time);
//             }
//         }
//         // retry logic
        // if (req->retry_left > 0) {
        //     req->retry_left -= 1;
        //     double backoff = 10.0;
        //     auto ev = make_unique<Event>(time + backoff,event_type::USER_ARRIVAL,req->user_id);
        //     push_event(std::move(ev));
        // }
//     }
// }

void Simulator::release_thread_to_pool(ThreadWorker* th,double now) {
    qsys.release_thread_to_pool(th,now);
}

Result Simulator::run(double simtime,double warmup_time,unsigned seed,int runid,bool trace_on) {
    run_id = runid;
    reset_for_run(seed);
    if(cores.empty()){
        make_cores(common::NUM_CORES);
    }
    qsys.set_cores(cores);
    schedule_initial_users(common::NUM_USERS);
    while (true) {
        auto ev = pop_event();
        if (!ev) break;
        now = ev->time;

        if (now > simtime) break;

        switch (ev->type) {
            case event_type::USER_ARRIVAL:
                handle_user_arrival(ev->user_id);
                break;
            case event_type::THREAD_SLICE_START:
                handle_thread_slice_start(ev->thread,ev->core,now);
                break;
            case event_type::THREAD_SLICE_END:
                handle_thread_slice_end(ev->thread,ev->core,ev->slice_len,now);
                break;
            case event_type::REQUEST_COMPLETE:
                handle_request_complete(ev->req,now);
                break;
            // case event_type::REQUEST_TIMEOUT:
            //     handle_request_timeout(ev->req,now);
            //     break;
            case event_type::THREAD_AVAILABLE:
                handle_thread_available(ev->thread,ev->core,now);
                break;
            default:
                break;
        }
    }

    vector<double> resp_times;
    int good = 0,bad = 0;
    for (auto r : completed_requests) {
        if (r->completion_time >= warmup_time) {
            double rt = r->response_time();
            resp_times.push_back(rt);
            good++;
        }
    }
    for(auto r: timedout_requests){
        if(r->completion_time >= warmup_time){
            double rt = r->response_time();
            resp_times.push_back(rt);
            bad++;
        }
    }
    double avg_rt = -1.0;
    if (!resp_times.empty()) {
        double sum=0;
        for (double x: resp_times) sum += x;
        avg_rt = sum / resp_times.size();
    }
    double utilization=0.0;
    for(auto core: cores){
        utilization+= core->busy_time;
    }
    utilization /= max(1,(int)common::NUM_CORES);
    utilization/= max(1.0,(simtime-warmup_time));
    double interval = max(1.0,simtime - warmup_time);
    double throughput = (double) (good + bad) / interval;
    double goodput = (double) good / interval;
    double badput = (double) bad / interval;
    // cerr<< bad<<" "<<interval<<endl;

    if (trace_on) write_trace(runid);

    Result res;
    res.avg_response_time = avg_rt;
    res.throughput = throughput;
    res.goodput = goodput;
    res.badput = badput;
    res.completed = (int)completed_requests.size();
    res.timedout = (int)timedout_requests.size();
    res.dropped = dropped_requests;
    res.util = utilization;
    return res;
}

void Simulator::write_trace(int runid) {
    filesystem::create_directories("runs");
    ostringstream fname;
    fname << common::TRACE_PREFIX << "_" << runid << ".csv";
    ofstream ofs(fname.str());
    ofs << "event,time,req_id,user_id,val1,val2\n";
    for (auto &line : trace_lines) {
        ofs << line << "\n";
    }
    ofs.close();
}