# Simulator Documentation

## Overview
This simulator implements a discrete event simulation system with a queueing system, event handling, and multi-threaded request processing.

---

## Classes and Methods

### 1. **Event** (`event.h`)
Represents a discrete event in the simulation system.

#### Class Members
- `type`: Event type identifier
- `timestamp`: Time when the event occurs
- `request_id`: Associated request identifier

#### Methods
- **Event()**: Default constructor, initializes event with default values
- **Event(int type, double timestamp, int request_id)**: Parameterized constructor to create an event with specified type, timestamp, and request ID

---

### 2. **Request** (`request.h`)
Represents a request being processed through the queueing system.

#### Class Members
- `id`: Unique request identifier
- `arrival_time`: Time when request enters the system
- `service_time`: Duration required to process the request
- `completion_time`: Time when request finishes processing
- `start_time`: Time when request begins service

#### Methods
- **Request()**: Default constructor
- **Request(int id, double arrival_time, double service_time)**: Parameterized constructor to initialize request with ID, arrival time, and service time

---

### 3. **Common** (`common.h`)
Contains common constants and utilities shared across the simulator.

#### Constants
- Event type definitions (ARRIVAL, DEPARTURE, etc.)
- System configuration parameters
- Time constants

#### Methods
- Utility functions for common operations

---

### 4. **QueueingSystem** (`queueing_system.h`, `queueing_system.cpp`)
Core queueing system managing request queues and server states.

#### Class Members
- `queue`: Request queue for pending requests
- `busy_servers`: Count of currently occupied servers
- `total_servers`: Total number of available servers
- `statistics`: Accumulated system statistics

#### Methods
- **QueueingSystem(int num_servers)**: Constructor initializing the queueing system with specified number of servers
- **void enqueue(Request request)**: Add a request to the queue
- **Request dequeue()**: Remove and return the next request from the queue
- **bool is_queue_empty()**: Check if queue has no pending requests
- **int get_queue_size()**: Return current queue length
- **void mark_server_busy()**: Increment busy server count
- **void mark_server_free()**: Decrement busy server count
- **int get_available_servers()**: Return number of free servers
- **void update_statistics(Request request)**: Update system statistics based on completed request

---

### 5. **Simulator** (`simulator.h`, `simulator.cpp`)
Main simulation engine orchestrating the discrete event simulation.

#### Class Members
- `event_queue`: Priority queue of events ordered by timestamp
- `queueing_system`: The queueing system being simulated
- `current_time`: Current simulation time
- `total_events`: Count of events processed
- `statistics`: Simulation statistics and metrics

#### Methods
- **Simulator(int num_servers)**: Constructor initializing simulator with specified number of servers
- **void schedule_event(Event event)**: Add an event to the event queue for future processing
- **Event get_next_event()**: Retrieve and remove the next event from the queue
- **void process_event(Event event)**: Handle the specified event based on its type
- **void handle_arrival(Event event)**: Process arrival events (new requests enter system)
- **void handle_departure(Event event)**: Process departure events (requests complete service)
- **void run(double simulation_end_time)**: Execute simulation until specified end time
- **void print_statistics()**: Output simulation results and performance metrics

---

### 6. **ThreadWorker** (`threadworker.h`)
Thread pool worker for parallel request processing.

#### Class Members
- `thread_id`: Unique worker identifier
- `is_busy`: Current worker availability status
- `assigned_request`: Request currently being processed

#### Methods
- **ThreadWorker(int id)**: Constructor creating worker with specified thread ID
- **void assign_request(Request request)**: Assign a request to this worker
- **void process_request()**: Execute processing on the assigned request
- **void mark_idle()**: Mark worker as available for new assignments
- **bool is_available()**: Check if worker is available for work
- **int get_thread_id()**: Return the worker's thread identifier

---

### 7. **Core** (`core.h`, `core.cpp`)
Central orchestration layer coordinating simulation components.

#### Class Members
- `simulator`: Main simulator instance
- `thread_workers`: Pool of worker threads
- `num_workers`: Total number of worker threads

#### Methods
- **Core(int num_servers, int num_workers)**: Constructor initializing core with server and worker thread counts
- **void initialize()**: Set up simulation components and thread pool
- **void execute(double simulation_time)**: Run the complete simulation
- **void shutdown()**: Clean up resources and finalize simulation
- **void print_results()**: Output final simulation results and statistics

---

### 8. **Main Entry Point** (`main.cpp`)
Application entry point for launching the simulator.

#### Methods
- **int main(int argc, char* argv[])**: Main function parsing command-line arguments and initiating simulation
  - Accepts parameters for: number of servers, number of workers, simulation duration
  - Initializes Core system
  - Executes simulation
  - Displays results

---

## Simulation Flow

1. **Initialization**: Create Core with specified servers and workers
2. **Scheduling**: Generate initial arrival events
3. **Event Processing Loop**: 
   - Extract next event from queue
   - Update simulation time
   - Process event (arrival/departure)
   - Schedule new events as needed
4. **Completion**: Output statistics and results

## Key Features

- Discrete event simulation with priority-based event processing
- Multi-server queueing system
- Thread worker pool for parallel processing
- Comprehensive statistics tracking
- FIFO queue management

---