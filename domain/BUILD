load("@build_stack_rules_proto//python:python_proto_library.bzl", "python_proto_library")
load("@rules_pkg//:pkg.bzl", "pkg_tar")

proto_library(
    name = "messages_proto",
    srcs = ["protobuf/messages.proto"],
)

python_proto_library(
    name = "messages_python_proto",
    deps = [":messages_proto"],
)

pkg_tar(
    name = "python_messages_tarball",
    strip_prefix = "protobuf/",
    package_dir = "ibidem/codetanks/domain",
    srcs = [":messages_python_proto"],
)

filegroup(
    name = "python_domain_files",
    srcs = glob([
        "python/**/*.py",
    ]),
)

pkg_tar(
    name = "python_domain_tarball",
    strip_prefix = "python/",
    srcs = [":python_domain_files"],
)

py_library(
    name = "python",
    deps = [
        ":python_domain_tarball",
        ":python_messages_tarball",
    ],
)
