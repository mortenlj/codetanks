load("@rules_python//python:defs.bzl", "py_test")
load("@server_test_deps//:requirements.bzl", "all_requirements")

def generate_test_rules():
    test_sources = native.glob(["tests/**/test_*.py"])
    for ts in test_sources:
        py_test(
            name = ts[6:-3],
            srcs = [
                ts,
                ":tests/run.py",
            ],
            deps = [":codetanks-server"] + all_requirements,
            main = ":tests/run.py",
            args = [native.package_name(), ts],
        )
