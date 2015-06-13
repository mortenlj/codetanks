package ibidem.gradle.python

import org.gradle.api.DefaultTask
import org.gradle.api.tasks.TaskAction

class TestPython extends DefaultTask {
    public static final String NAME = 'testPython'

    String testDir

    TestPython() {
        description = 'Run Python tests'
    }

    @TaskAction
    def test() {
        project.exec {
            environment["NOSE_WHERE"] = "src/test/python"
            executable = 'nosetests'
        }
    }
}
