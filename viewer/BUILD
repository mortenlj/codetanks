load("@rules_python//python:defs.bzl", "py_library")
load("@viewer_py_deps//:requirements.bzl", "all_requirements")

filegroup(
    name = "viewer_files",
    srcs = glob([
        "ibidem/**/*.py",
    ]),
)

filegroup(
    name = "viewer_data",
    srcs = glob([
        "ibidem/codetanks/viewer/resources/*",
    ]),
)

py_library(
    name = "viewer_lib",
    deps = [
        "//domain/python:messages",
    ] + all_requirements,
    imports = ["."],
)

py_binary(
    name = "codetanks-viewer",
    main = "ibidem/codetanks/viewer/main.py",
    args = ["tcp://localhost:13337"],
    data = [":viewer_data"],
    srcs = [":viewer_files"],
    deps = [":viewer_lib"],
)
