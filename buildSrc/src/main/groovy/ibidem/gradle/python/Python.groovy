package ibidem.gradle.python

import org.gradle.api.Project
import org.gradle.api.artifacts.dsl.DependencyHandler
import org.gradle.api.internal.artifacts.dsl.dependencies.DefaultDependencyHandler
import org.gradle.util.ConfigureUtil

class Python {
    DependencyHandler dependencyHandler
    BuildPythonTask build

    Python(Project project, BuildPythonTask build) {
        dependencyHandler = new DefaultDependencyHandler(
                project.getConfigurations(),
                new PythonDependencyFactory(),
                null, // TODO
                null, // TODO
                null, // TOOD
                null  // TODO
        )
        this.build = build
    }

    void dependencies(Closure config) {
        ConfigureUtil.configure(config, dependencyHandler)
    }

    void srcDir(def dir) {
        build.inputs.source(dir)
    }

    void collector(Closure collector) {
        build.collector = collector
    }
}
