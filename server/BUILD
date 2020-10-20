load("@rules_python//python:defs.bzl", "py_library", "py_binary")
load("@server_py_deps//:requirements.bzl", "all_requirements")
load(":defs.bzl", "generate_test_rules")

filegroup(
    name = "server_files",
    srcs = glob([
        "ibidem/**/*.py",
    ]),
)

py_library(
    name = "server_lib",
    deps = [
        "//domain/python:messages",
    ] + all_requirements,
    imports = ["."],
)

py_binary(
    name = "codetanks-server",
    main = "ibidem/codetanks/server/main.py",
    srcs = [":server_files"],
    deps = [":server_lib"],
)

py_binary(
    name = "codetanks-bot",
    main = "ibidem/codetanks/server/cli_bot.py",
    srcs = [":server_files"],
    deps = [":server_lib"],
)

generate_test_rules()
