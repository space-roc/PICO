cmake_minimum_required(VERSION 3.21)

if(DEFINED ENV{PICO_SDK_PATH} AND NOT DEFINED PICO_SDK_PATH)
    set(PICO_SDK_PATH "$ENV{PICO_SDK_PATH}" CACHE PATH "Path to the Raspberry Pi Pico SDK")
endif()

if(NOT PICO_SDK_PATH)
    find_file(PICO_SDK_IMPORT_FILE
        NAMES "pico_sdk_import.cmake"
        PATHS
            "$ENV{USERPROFILE}/pico/pico-sdk"
            "$ENV{USERPROFILE}/src/pico-sdk"
            "$ENV{HOME}/pico/pico-sdk"
            "$ENV{HOME}/src/pico-sdk"
            "C:/Users/$ENV{USERNAME}/pico-sdk"
            "C:/Users/$ENV{USERNAME}/src/pico-sdk"
            "C:/Program Files/Raspberry Pi/Pico SDK"
            "C:/Program Files/Pico SDK"
        PATH_SUFFIXES "external"
        NO_DEFAULT_PATH
    )

    if(PICO_SDK_IMPORT_FILE)
        get_filename_component(PICO_SDK_PATH "${PICO_SDK_IMPORT_FILE}" DIRECTORY)
        get_filename_component(PICO_SDK_PATH "${PICO_SDK_PATH}" DIRECTORY)
    endif()
endif()

if(NOT PICO_SDK_PATH)
    message(FATAL_ERROR
        "Pico SDK not found. Set PICO_SDK_PATH to your SDK directory or install the Raspberry Pi Pico SDK, then rerun CMake."
    )
endif()

include("${PICO_SDK_PATH}/external/pico_sdk_import.cmake")

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
