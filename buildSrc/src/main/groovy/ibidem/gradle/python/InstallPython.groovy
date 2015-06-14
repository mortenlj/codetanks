package ibidem.gradle.python

import org.gradle.api.Task

class InstallPython extends AbstractSetupTask {
    public static final String NAME = 'installPython'

    Map<String, File> paths

    InstallPython() {
        description = 'Install python module'
    }

    @Override
    Task configure(Closure closure) {
        def task = super.configure(closure)
        inputs.source(paths.buildTarget)
        outputs.dir(paths.distFinal)
        return task
    }

    @Override
    def getCommand() {
        'install'
    }
}
