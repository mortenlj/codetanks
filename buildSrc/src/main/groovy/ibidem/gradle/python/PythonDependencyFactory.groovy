package ibidem.gradle.python

import org.gradle.api.artifacts.ClientModule
import org.gradle.api.artifacts.Dependency
import org.gradle.api.artifacts.ProjectDependency
import org.gradle.api.internal.artifacts.dsl.dependencies.DependencyFactory
import org.gradle.api.internal.artifacts.dsl.dependencies.ProjectFinder

class PythonDependencyFactory implements DependencyFactory {
    @Override
    Dependency createDependency(Object dependencyNotation) {
        def dep = dependencyNotation.toString()
        if (dep.contains('==')) {
            def parts = dep.split('==')
            new PythonDependency(parts.first(), parts.last())
        } else {
            new PythonDependency(dep)
        }
    }

    @Override
    ClientModule createModule(Object dependencyNotation, Closure configureClosure) {
        throw new IllegalStateException("Not supported!")
    }

    @Override
    ProjectDependency createProjectDependencyFromMap(ProjectFinder projectFinder, Map<? extends String, ? extends Object> map) {
        throw new IllegalStateException("Not supported!")
    }
}
