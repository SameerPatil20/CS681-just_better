CXX = g++
CXXFLAGS = -std=c++17 -O2 -Wall -Wextra
OBJS = main.o simulator.o core.o queueing_system.o

all: websim

websim: $(OBJS)
	$(CXX) $(CXXFLAGS) -o websim $(OBJS)

main.o: main.cpp simulator.h
	$(CXX) $(CXXFLAGS) -c main.cpp

simulator.o: simulator.cpp simulator.h common.h event.h request.h threadworker.h core.h queueing_system.h
	$(CXX) $(CXXFLAGS) -c simulator.cpp

# event.o: event.h
# 	$(CXX) $(CXXFLAGS) -c event.cpp

core.o: core.cpp core.h event.h simulator.h
	$(CXX) $(CXXFLAGS) -c core.cpp

queueing_system.o: queueing_system.cpp queueing_system.h simulator.h threadworker.h request.h
	$(CXX) $(CXXFLAGS) -c queueing_system.cpp

clean:
	rm -f websim *.o runs/*.csv