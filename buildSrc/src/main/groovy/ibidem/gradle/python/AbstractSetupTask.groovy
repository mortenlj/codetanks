package ibidem.gradle.python

import org.gradle.api.DefaultTask
import org.gradle.api.logging.LogLevel
import org.gradle.api.tasks.TaskAction

abstract class AbstractSetupTask extends DefaultTask {
    Map<String, File> paths

    @TaskAction
    def action() {
        logging.captureStandardOutput LogLevel.INFO
        project.exec {
            executable 'python'
            workingDir paths.root
            args = [paths.setup, command]
        }
    }

    abstract getCommand();
}
