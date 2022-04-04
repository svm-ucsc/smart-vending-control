cmake_minimum_required(VERSION 2.8.12)
project(ItemLaneSystem)

find_package(pybind11 REQUIRED)
pybind11_add_module(ItemLaneSystem ItemLaneSystem.cpp)
target_link_libraries(ItemLaneSystem PRIVATE -lwiringPi -pthread)
