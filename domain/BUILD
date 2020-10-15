load("@build_stack_rules_proto//python:python_proto_library.bzl", "python_proto_library")
load("@rules_pkg//:pkg.bzl", "pkg_tar")
load("@rules_python//python:defs.bzl", "py_library")
load("@rules_python//experimental/python:wheel.bzl", "py_package", "py_wheel")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")

proto_library(
    name = "messages_proto",
    srcs = ["protobuf/messages.proto"],
)

python_proto_library(
    name = "messages_python_proto",
    deps = [":messages_proto"],
)

copy_file(
    name="python_messages_files",
    src=":messages_python_proto",
    out="ibidem/codetanks/domain/messages_pb2.py",
)

filegroup(
    name = "python_domain_files",
    srcs = glob([
        "python/**/__init__.py",
    ]),
)

py_library(
    name = "python",
    srcs = [
        ":python_domain_files",
        ":python_messages_files",
    ],
)

py_package(
    name = "python_pkg",
    deps = [
        ":python",
    ],
)

py_wheel(
    name = "python_whl",
    distribution = "codetanks-domain",
    version = "0.0.1",
    deps = [":python_pkg"],
    strip_path_prefixes=[
        "domain/python",
        "domain",
    ],
)
