load("@build_stack_rules_proto//python:python_proto_library.bzl", "python_proto_library")
load("@rules_python//python:defs.bzl", "py_library")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")

copy_file(
    name="python_messages_file",
    src="//domain/protobuf:python_messages_proto",
    out="ibidem/codetanks/domain/messages_pb2.py",
)

filegroup(
    name = "python_helper_files",
    srcs = glob([
        "ibidem/**/__init__.py",
    ]),
)

py_library(
    name = "messages",
    srcs = [
        ":python_helper_files",
        ":python_messages_file",
    ],
    imports = ["."],
    visibility = ["//visibility:public"]
)
