# Generic pre-reqs
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# python
http_archive(
    name = "rules_python",
    sha256 = "ddb2e1298684defde2f5e466d96e572119f30f9e2a901a7a81474fd4fa9f6d52",
    strip_prefix = "rules_python-dd7f9c5f01bafbfea08c44092b6b0c8fc8fcb77f",
    urls = [
        "https://github.com/bazelbuild/rules_python/archive/dd7f9c5f01bafbfea08c44092b6b0c8fc8fcb77f.zip",
    ],
)
load("@rules_python//python:pip.bzl", "pip_import", "pip_repositories")
pip_repositories()
load("@rules_python//python:repositories.bzl", "py_repositories")
py_repositories()

# protobuf
http_archive(
    name = "build_stack_rules_proto",
    urls = ["https://github.com/stackb/rules_proto/archive/b2913e6340bcbffb46793045ecac928dcf1b34a5.tar.gz"],
    sha256 = "d456a22a6a8d577499440e8408fc64396486291b570963f7b157f775be11823e",
    strip_prefix = "rules_proto-b2913e6340bcbffb46793045ecac928dcf1b34a5",
)

load("@build_stack_rules_proto//python:deps.bzl", "python_proto_library")
python_proto_library()

pip_import(
    name = "protobuf_py_deps",
    requirements = "@build_stack_rules_proto//python/requirements:protobuf.txt",
)

load("@protobuf_py_deps//:requirements.bzl", protobuf_pip_install = "pip_install")
protobuf_pip_install()

# pkg
http_archive(
    name = "rules_pkg",
    url = "https://github.com/bazelbuild/rules_pkg/releases/download/0.2.5/rules_pkg-0.2.5.tar.gz",
    sha256 = "352c090cc3d3f9a6b4e676cf42a6047c16824959b438895a76c2989c6d7c246a",
)
load("@rules_pkg//:deps.bzl", "rules_pkg_dependencies")
rules_pkg_dependencies()

#skylib
http_archive(
    name = "bazel_skylib",
    sha256 = "97e70364e9249702246c0e9444bccdc4b847bed1eb03c5a3ece4f83dfe6abc44",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/bazel-skylib/releases/download/1.0.2/bazel-skylib-1.0.2.tar.gz",
        "https://github.com/bazelbuild/bazel-skylib/releases/download/1.0.2/bazel-skylib-1.0.2.tar.gz",
    ],
)
load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")
bazel_skylib_workspace()
