package ibidem.gradle.python

import org.gradle.api.artifacts.Dependency

class PythonDependency implements Dependency {
    String name
    String version

    PythonDependency(String name, String version) {
        this.name = name
        this.version = version
    }

    PythonDependency(String name) {
        this(name, null)
    }

    String getPythonReq() {
        name + (version != null ? "==${version}" : '')
    }

    @Override
    String getGroup() {
        return null // Python does not use groups
    }

    @Override
    boolean contentEquals(Dependency dependency) {
        return name == dependency.name && version == dependency.version
    }

    @Override
    Dependency copy() {
        return new PythonDependency(name, version)
    }

    @Override
    public String toString() {
        return """\
PythonDependency{
    name='$name',
    version='$version'
}"""
    }
}
