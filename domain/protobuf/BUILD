package(default_visibility=["//domain:__subpackages__"])

load("@build_stack_rules_proto//python:python_proto_library.bzl", "python_proto_library")

proto_library(
    name = "messages_proto",
    srcs = ["messages.proto"],
)

python_proto_library(
    name = "python_messages_proto",
    deps = [":messages_proto"],
)
