# Generic pre-reqs
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# python
http_archive(
    name = "rules_python",
    url = "https://github.com/bazelbuild/rules_python/releases/download/0.1.0/rules_python-0.1.0.tar.gz",
    sha256 = "b6d46438523a3ec0f3cead544190ee13223a52f6a6765a29eae7b7cc24cc83a0",
)
load("@rules_python//python:pip.bzl", "pip_install")
load("@rules_python//python:repositories.bzl", "py_repositories")
py_repositories()

# Stand alone Python interpreter

PYTHON_VERSION = "3.8.3"
PYTHON_SHA256 = "dfab5ec723c218082fe3d5d7ae17ecbdebffa9a1aea4d64aa3a2ecdd2e795864"

# Special logic for building python interpreter with OpenSSL from homebrew.
# See https://devguide.python.org/setup/#macos-and-os-x
_py_configure = """
if [[ "$OSTYPE" == "darwin"* ]]; then
    ./configure --prefix=$(pwd)/bazel_install --with-openssl=$(brew --prefix openssl)
else
    ./configure --prefix=$(pwd)/bazel_install
fi
"""

http_archive(
    name = "python_interpreter",
    urls = ["https://www.python.org/ftp/python/%s/Python-%s.tar.xz" % (PYTHON_VERSION, PYTHON_VERSION)],
    sha256 = PYTHON_SHA256,
    strip_prefix = "Python-%s" % PYTHON_VERSION,
    patch_cmds = [
        "mkdir $(pwd)/bazel_install",
        _py_configure,
        "make",
        "make install",
        "ln -s bazel_install/bin/python3 python_bin",
    ],
    build_file_content = """
exports_files(["python_bin"])
filegroup(
    name = "files",
    srcs = glob(["bazel_install/**"], exclude = ["**/* *"]),
    visibility = ["//visibility:public"],
)
""",
)

register_toolchains("//:py3_toolchain")

# protobuf
http_archive(
    name = "build_stack_rules_proto",
    urls = ["https://github.com/stackb/rules_proto/archive/b2913e6340bcbffb46793045ecac928dcf1b34a5.tar.gz"],
    sha256 = "d456a22a6a8d577499440e8408fc64396486291b570963f7b157f775be11823e",
    strip_prefix = "rules_proto-b2913e6340bcbffb46793045ecac928dcf1b34a5",
)

load("@build_stack_rules_proto//python:deps.bzl", "python_proto_library")
python_proto_library()

pip_install(
    name = "protobuf_py_deps",
    requirements = "@build_stack_rules_proto//python/requirements:protobuf.txt",
    python_interpreter_target = "@python_interpreter//:python_bin",
)

pip_install(
    name = "viewer_py_deps",
    requirements = "//viewer:bazel_reqs.txt",
    python_interpreter_target = "@python_interpreter//:python_bin",
)

pip_install(
    name = "server_py_deps",
    requirements = "//server:bazel_reqs.txt",
    python_interpreter_target = "@python_interpreter//:python_bin",
)

pip_install(
    name = "server_test_deps",
    requirements = "//server:bazel_test_reqs.txt",
    python_interpreter_target = "@python_interpreter//:python_bin",
)

# skylib
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

# java
RULES_JVM_EXTERNAL_TAG = "2.8"
RULES_JVM_EXTERNAL_SHA = "79c9850690d7614ecdb72d68394f994fef7534b292c4867ce5e7dec0aa7bdfad"

http_archive(
    name = "rules_jvm_external",
    strip_prefix = "rules_jvm_external-%s" % RULES_JVM_EXTERNAL_TAG,
    sha256 = RULES_JVM_EXTERNAL_SHA,
    url = "https://github.com/bazelbuild/rules_jvm_external/archive/%s.zip" % RULES_JVM_EXTERNAL_TAG,
)

load("@rules_jvm_external//:defs.bzl", "maven_install")
maven_install(
    artifacts = [
        "com.google.code.findbugs:jsr305:1.3.9",
        "com.google.errorprone:error_prone_annotations:2.0.18",
        "com.google.j2objc:j2objc-annotations:1.1",
        "org.zeromq:jeromq:0.3.4",
        "org.apache.logging.log4j:log4j-api:2.2",
        "org.apache.logging.log4j:log4j-core:2.2",
        "org.apache.logging.log4j:log4j-slf4j-impl:2.2",
    ],
    repositories = [
        "https://jcenter.bintray.com/",
        "https://repo1.maven.org/maven2",
    ],
)

# groovy
http_archive(
    name = "io_bazel_rules_groovy",
    url = "https://github.com/bazelbuild/rules_groovy/archive/0.0.6.tar.gz",
    sha256 = "21c7172786623f280402d3b3a2fc92f36568afad5a4f6f5ea38fd1c6897aecf8",
    strip_prefix = "rules_groovy-0.0.6",
)
load("@io_bazel_rules_groovy//groovy:repositories.bzl", "rules_groovy_dependencies")
rules_groovy_dependencies()
