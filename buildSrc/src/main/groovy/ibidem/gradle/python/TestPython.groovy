package ibidem.gradle.python

import org.gradle.api.DefaultTask
import org.gradle.api.tasks.TaskAction

class TestPython extends DefaultTask {
    public static final String NAME = 'testPython'
    private static final String TEST_SOURCES = "src/test/python"

    TestPython() {
        description = 'Run Python tests'
    }

    @TaskAction
    def test() {
        def testDir = project.file(TEST_SOURCES)
        if (testDir.exists()) {
            project.exec {
                environment["NOSE_WHERE"] = TEST_SOURCES
                executable = 'nosetests'
            }
        }
    }
}
