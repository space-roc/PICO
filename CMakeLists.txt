cmake_minimum_required(VERSION 3.21)

if(NOT DEFINED ENV{PICO_SDK_PATH})
    message(FATAL_ERROR "Set the PICO_SDK_PATH environment variable to your Pico SDK directory.")
endif()

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(pico_workspace C CXX ASM)

pico_sdk_init()

add_executable(pico_workspace
    src/main.c
)

target_link_libraries(pico_workspace
    pico_stdlib
)

pico_enable_stdio_usb(pico_workspace 1)
pico_enable_stdio_uart(pico_workspace 0)

pico_add_extra_outputs(pico_workspace)
