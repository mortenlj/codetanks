
load("@io_bazel_rules_groovy//groovy:groovy.bzl", "groovy_binary")

groovy_binary(
    name = "Randomizer",
    srcs = glob(["src/main/groovy/**/*.groovy"]),
    main_class = "ibidem.codetanks.sample.groovy.Randomizer",
    resources = glob(["src/main/resources/**"]),
    deps = [
         "//domain/java:messages",
         "@maven//:org_zeromq_jeromq",
         "@maven//:org_apache_logging_log4j_log4j_api",
         "@maven//:org_apache_logging_log4j_log4j_core",
         "@maven//:org_apache_logging_log4j_log4j_slf4j_impl",
    ],
)
