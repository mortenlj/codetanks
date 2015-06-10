package ibidem.gradle.python

import org.gradle.api.DefaultTask
import org.gradle.api.tasks.TaskAction

class BuildPython extends DefaultTask {
    public static final String NAME = 'buildPython'

    String outputDir

    BuildPython() {
        description = 'Build the python library'
    }

    @TaskAction
    def build() {
        project.exec {
            executable = 'python'
            args = ['setup.py', 'build', '-b', outputDir]
        }
    }
}
