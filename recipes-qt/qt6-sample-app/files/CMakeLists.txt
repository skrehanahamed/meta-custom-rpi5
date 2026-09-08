cmake_minimum_required(VERSION 3.16)
project(qt6-sample-app LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets Network)

qt_standard_project_setup()

qt_add_executable(qt6-sample-app
    main.cpp
)

target_link_libraries(qt6-sample-app PRIVATE
    Qt6::Core
    Qt6::Gui
    Qt6::Widgets
    Qt6::Network
)

install(TARGETS qt6-sample-app DESTINATION bin)
