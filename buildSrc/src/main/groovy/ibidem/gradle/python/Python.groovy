package ibidem.gradle.python

import org.gradle.api.Project
import org.gradle.api.artifacts.dsl.DependencyHandler
import org.gradle.api.internal.artifacts.dsl.dependencies.DefaultDependencyHandler
import org.gradle.util.ConfigureUtil

class Python {
    DependencyHandler dependencyHandler

    Python(Project project) {
        dependencyHandler = new DefaultDependencyHandler(
                project.getConfigurations(),
                new PythonDependencyFactory(),
                null, // TODO
                null, // TODO
                null, // TOOD
                null  // TODO
        )
    }

    void dependencies(Closure config) {
        ConfigureUtil.configure(config, dependencyHandler)
    }
}
