all:
	g++ -std=c++11 -Wall -o stepper_test stepper_test.cpp -lwiringPi -pthread
	g++ -std=c++11 -Wall -o lane_c_test ItemLaneSystem.cpp -lwiringPi -pthread

clean:
	rm stepper_test lane_c_test
