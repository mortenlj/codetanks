package ibidem.gradle.python

import org.gradle.api.Task

class BuildPython extends AbstractSetupTask {
    public static final String NAME = 'buildPython'

    Map<String, File> paths

    BuildPython() {
        description = 'Build the python library'
    }

    @Override
    Task configure(Closure closure) {
        def task = super.configure(closure)
        inputs.source(paths.collectedSources)
        outputs.dir(paths.buildTarget)
        return task
    }

    @Override
    def getCommand() {
        'build'
    }
}
