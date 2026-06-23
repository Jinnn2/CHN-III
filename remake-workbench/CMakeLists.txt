cmake_minimum_required(VERSION 3.20)

project(China2EXRebuild C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

add_executable(china2ex_rebuild WIN32
    src/main.c
    src/app.c
)

target_include_directories(china2ex_rebuild PRIVATE src)

if(MINGW)
    target_link_libraries(china2ex_rebuild PRIVATE gdi32)
endif()
